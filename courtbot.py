import json
import logging
import os
import re
from datetime import datetime, timedelta
from functools import partial
from logging.config import dictConfig

import requests
from bs4 import BeautifulSoup
from flask import abort, Flask, jsonify, request
from pytz import timezone
from slackclient import SlackClient
from zappa.async import task


dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{asctime} {levelname} {process} [{filename}:{lineno}] - {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'werkzeug': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
})

logger = logging.getLogger(__name__)
slack = SlackClient(os.environ['SLACK_API_TOKEN'])
app = Flask(__name__)


def is_request_valid(request):
    """
    Verify that the request was issued by Slack.
    """
    is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
    is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

    return is_token_valid and is_team_id_valid


def now():
    return datetime.now(tz=timezone('America/New_York'))


def to_24(twelve_hour_string):
    """
    Convert a string representing an hour on a 12-hour clock into an integer
    hour on a 24-hour clock.
    """
    clocks = {now().replace(hour=hour).strftime('%-I %p'): hour for hour in range(24)}

    return clocks[twelve_hour_string]


def to_hours(raw, is_tomorrow):
    """
    Convert raw court availability data to a dict of available hours keyed by
    court number. This function expects an array of raw court availability dicts
    as returned by the scheduling API, each looking like:

    {
      'Id': 17,
      'Availability': [
        {'IsAvailable': False, 'TimeId': 0},
        {'IsAvailable': False, 'TimeId': 1},
        ...
        {'IsAvailable': False, 'TimeId': 1439},
      ]
    }
    """
    courts = {}
    hours_as_minutes = {hour * 60 for hour in range(24)}

    for court in raw:
        hours = []
        minutes = court['Availability']

        for minute in minutes:
            if (minute['TimeId'] in hours_as_minutes) and minute['IsAvailable']:
                hour = minute['TimeId'] / 60

                # Exclude times that are in the past unless asked for times tomorrow.
                if (hour > now().hour) or is_tomorrow:
                    hours.append(int(hour))

        if hours:
            # Join array of integers representing hours on a 24-hour clock into
            # string of comma-separated hours on a 12-hour clock.
            formatted = [now().replace(hour=hour).strftime('%-I %p') for hour in hours]
            courts[court['Id'] - 16] = ', '.join(formatted)

    return courts


class Scheduler:
    def __init__(self, request_text):
        self.request_text = request_text
        self.is_tomorrow = 'tomorrow' in self.request_text
        self.tomorrow = ' tomorrow' if self.is_tomorrow else ''

        mit_recreation_usernames = os.environ['MIT_RECREATION_USERNAMES'].split(',')
        mit_recreation_passwords = os.environ['MIT_RECREATION_PASSWORDS'].split(',')
        self.credentials = zip(mit_recreation_usernames, mit_recreation_passwords)

        self.base_url = 'https://east-a-60ols.csi-cloudapp.net'

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/60.0.3112.90 Safari/537.36'
            )
        })

    def look(self, conversational=True):
        """
        Retrieve court availability data.

        Data comes from the same API used by the MIT Recreation scheduling
        application. Accessing it doesn't require authentication. Courts can
        only be booked by the hour, but the API returns minute-by-minute court
        availability. ಠ_ಠ
        """
        url = f'{self.base_url}/MIT/Library/OlsService.asmx/GetSchedulerResourceAvailability'

        date = now() + timedelta(days=int(self.is_tomorrow))
        data = {
            'siteId': '1261',
            # Each court has a resource ID. Z-Center courts 1-5 have resource IDs 17-21.
            'resourceIds': list(range(17, 22)),
            'selectedDate': date.strftime('%m/%d/%Y'),
        }

        response = self.session.post(url, json=data)

        raw = response.json()['d']['Value']
        courts = to_hours(raw, self.is_tomorrow)

        if conversational:
            if courts:
                message = [f"Here's how the courts look{self.tomorrow}."]

                for court_number, hours in courts.items():
                    message.append(f'*#{court_number}* is available at {hours}.')

                return '\n\n'.join(message)
            else:
                return f'There are no courts available{self.tomorrow}.'
        else:
            return courts

    def book(self):
        pattern = r'#(?P<court_number>[1-5]).*(@|at) (?P<twelve_hour_time>[1-9]|1[012])\s*(?P<period>am|pm)'
        match = re.search(pattern, self.request_text, re.IGNORECASE)

        if match:
            logger.info('Request text matches booking pattern, ready to book')

            court_number = int(match.group('court_number'))
            twelve_hour_time = int(match.group('twelve_hour_time'))
            period = match.group('period').upper()

            hour = to_24(f'{twelve_hour_time} {period}')

            for username, password in self.credentials:
                pipeline = [
                    partial(self.login, username, password),
                    partial(self.stage, court_number, hour),
                    self.confirm,
                ]

                try:
                    success = True
                    for step in pipeline:
                        if success:
                            success = step()
                except:
                    logger.exception(f'Attempt to book as {username} failed')
                    continue

                if success:
                    return f"I've booked #{court_number} at {twelve_hour_time} {period}{self.tomorrow}."
            else:
                raise Exception('Credentials exhausted, unable to book')
        else:
            logger.info('Request text does not match booking pattern, aborting')
            return 'Please provide a court number and an hour (e.g., `/book #4 @ 8 pm`).'

    def login(self, username, password):
        """
        Login to the MIT Recreation website.
        """
        # For some unknown reason, this cookie won't be set if it's not present
        # before the login request is made. The value of the cookie is overwritten
        # during login. It's also worth noting that ASP.NET does not explicitly
        # couple a specific forms authentication cookie to an ASP.NET_SessionId.
        # Any valid forms authentication cookie can be used with any other valid
        # session cookie, unless the user's identity is manually added to the session
        # and compared with the identity tied to the forms auth cookie, which the
        # MIT Recreation website doesn't do.
        # http://blog.securityps.com/2013/06/session-fixation-forms-authentication.html?m=1
        domain = self.base_url.split('https://')[1]
        self.session.cookies.set('.CSIASPXFORMSAUTH', 'dummy', domain=domain)

        url = f'{self.base_url}/MIT/Login.aspx?AspxAutoDetectCookieSupport=1'

        with open('forms/login.json') as f:
            form = json.load(f)

        form['ctl00$pageContentHolder$loginControl$UserName'] = username
        form['ctl00$pageContentHolder$loginControl$Password'] = password

        response = self.session.post(url, data=form)

        if response.status_code == 200:
            logger.info(f'Logged in as {username}')
            return True
        else:
            logger.info(f'Failed to log in as {username}')
            return False

    def stage(self, court_number, hour):
        """
        Stage a court reservation. It must be confirmed separately. Hour should
        be an hour on a 24-hour clock.
        """
        url = f'{self.base_url}/MIT/Library/OlsService.asmx/SetScheduleInformation'

        date = now() + timedelta(days=int(self.is_tomorrow))
        schedule_data = {
            'ScheduleDate': date.strftime('%m/%d/%Y'),
            'Duration': 60,
            'Resource': f'Zesiger Squash Court #{court_number}',
            'Provider': '',
            'SiteId': 1261,
            'ProviderId': 0,
            # This resource ID must be a string. Don't ask me why.
            'ResourceId': str(court_number + 16),
            'ServiceId': 4,
            'ServiceName': 'Recreational Squash',
            'ServiceUniqueIdentifier': '757170ab-4338-4ff6-868d-2fb51cc449f8',
        }

        payload = {
            # The values for both of these keys need to be strings. (╯ಠ_ಠ）╯︵ ┻━┻
            'scheduleInformation': json.dumps(schedule_data, separators=(',', ':')),
            'startTime': str(hour * 60),
        }

        response = self.session.post(url, json=payload)

        if response.status_code == 200:
            logger.info('Staged reservation')
            return True
        else:
            logger.info('Failed to stage reservation')
            return False

    def confirm(self):
        """
        Confirm a staged court reservation.
        """
        url = f'{self.base_url}/MIT/Members/Scheduler/AddFamilyMembersScheduler.aspx?showOfflineMessage=true'
        response = self.session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        with open('forms/confirm.json') as f:
            form = json.load(f)

        form['__VIEWSTATE'] = soup.find(id='__VIEWSTATE').get('value')
        form['ctl00$rnHf'] = soup.find(id='ctl00_rnHf').get('value')

        response = self.session.post(url, data=form)

        soup = BeautifulSoup(response.text, 'html.parser')
        thank_you = soup.find(id='ctl00_pageContentHolder_lblThankYou').get_text()

        if thank_you:
            logger.info('Confirmed reservation!')
            return True
        else:
            logger.info('Failed to confirm reservation.')
            return False


@task
def look_task(request_text, response_url):
    logger.info(f'Executing look task with [{request_text}]')

    data = {
        'response_type': 'in_channel',
        'text': None,
    }

    try:
        data['text'] = Scheduler(request_text).look()
    except:
        logger.exception('Looking failed')
        data['text'] = 'Something went wrong. Sorry!'

    requests.post(response_url, json=data)


@task
def book_task(request_text, response_url):
    logger.info(f'Executing book task with [{request_text}]')

    data = {
        'response_type': 'in_channel',
        'text': None,
    }

    try:
        data['text'] = Scheduler(request_text).book()
    except:
        logger.exception('Booking failed')
        data['text'] = 'Something went wrong. Sorry!'

    requests.post(response_url, json=data)


@app.route('/look', methods=['POST'])
def look():
    if not is_request_valid(request):
        abort(400)

    request_text = request.form['text']
    if 'help' in request_text:
        response_text = (
            'Use this command to check squash court availability. '
            'Call it without arguments (i.e., `/look`) to check today. '
            'Call it with `tomorrow` as an argument (e.g., `/look tomorrow`) to check tomorrow.'
        )

        return jsonify(
            response_type='in_channel',
            text=response_text,
        )

    # Slack requires slash commands to respond in less than 3 seconds. Interactions
    # with the booking site can be long-running, so we perform them asynchronously.
    # This function call should return immediately.
    look_task(request_text, request.form['response_url'])

    return jsonify(
        response_type='in_channel',
        text='Looking...',
    )


@app.route('/book', methods=['POST'])
def book():
    if not is_request_valid(request):
        abort(400)

    request_text = request.form['text']
    if 'help' in request_text:
        response_text = (
            'Use this command to reserve a Z-Center squash court. '
            'Call it with a court number and an hour to make a reservation (e.g., `/book #4 @ 8 pm`). '
            'Include `tomorrow` as an argument (e.g., `/book #4 @ 8 pm tomorrow`) to book a court for tomorrow.'
        )

        return jsonify(
            response_type='in_channel',
            text=response_text,
        )

    book_task(request_text, request.form['response_url'])

    return jsonify(
        response_type='in_channel',
        text='Booking...',
    )


def scheduled_book():
    logger.info('Running scheduled book task')
    hours = [7, 8, 9]
    options = {hour: [] for hour in hours}

    try:
        slack.api_call(
            'chat.postMessage',
            channel='#general',
            text='Looking...'
        )
        courts = Scheduler('tomorrow').look(conversational=False)

        for court_number, court_hours in courts.items():
            for hour in hours:
                if f'{hour} PM' in court_hours:
                    options[hour].append(court_number)

        court = None
        for hour in hours:
            if options[hour]:
                # only move to another court if the one booked earlier isn't available
                if court not in options[hour]:
                    court = options[hour][0]

                message = Scheduler(f'#{court} at {hour} PM tomorrow').book()

                slack.api_call(
                    'chat.postMessage',
                    channel='#general',
                    text=message
                )
            else:
                slack.api_call(
                    'chat.postMessage',
                    channel='#general',
                    text=f'No courts available at {hour} PM tomorrow.'
                )
    except:
        logger.exception('Scheduled booking failed')
        slack.api_call(
            'chat.postMessage',
            channel='#general',
            text='Something went wrong. Sorry!'
        )