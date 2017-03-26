from collections import defaultdict
import logging
import re
from time import sleep

from slackclient import SlackClient
from slackclient._server import SlackConnectionError

from courtbot import constants, settings
from courtbot.spider import Spider
from courtbot.utils import conversational_join


logger = logging.getLogger(__name__)


class Bot:
    """
    Bot capable of reading from and writing to Slack.

    Uses Slack's RTM API. For more about the RTM API, see documentation at
    http://slackapi.github.io/python-slackclient/real_time_messaging.html.
    """
    def __init__(self):
        logger.info('Initializing courtbot.')

        self.client = SlackClient(settings.SLACK_TOKEN)
        self.spider = Spider()

        self.users = {}
        self.id = None
        self.cache_users()

        self.actions = {
            'health': [
                'alive',
                'health',
            ],
            'help': [
                'explain',
                'help',
            ],
            'show': [
                'available',
                'check',
                'look',
                'show',
            ],
            'book': [
                'book',
                'grab',
                'reserve',
            ],
        }

    def cache_users(self):
        """
        Cache team user info.

        Finds and caches user IDs and handles belonging to everyone on the Slack
        team, including the bot. The bot ID is used to identify messages which
        mention the bot. Other IDs are used to look up handles so the bot can
        mention other users in its messages.
        """
        users = self.client.api_call('users.list')['members']
        for user in users:
            id = user['id']
            handle = user['name']

            self.users[id] = handle

            if handle == settings.SLACK_HANDLE:
                self.id = id

                logger.info(f'Bot ID is [{self.id}].')

    def connect(self):
        """
        Connect to the Slack RTM API.
        """
        logger.info('Attempting to connect to Slack.')

        if self.client.rtm_connect():
            logger.info('Connected to Slack.')

            while True:
                events = self.read()

                try:
                    self.parse(events)
                except:
                    logger.exception('Event parsing failed.')

                sleep(settings.SLACK_RTM_READ_DELAY)
        else:
            logger.error('Failed to connect to Slack.')
            raise SlackConnectionError

    def read(self):
        """
        Read from the RTM websocket stream.

        See https://api.slack.com/rtm#events.

        Returns:
            defaultdict: Lists of events, keyed by type. Empty if no new events
                were found when reading the stream.
        """
        events = defaultdict(list)
        stream = self.client.rtm_read()

        for event in stream:
            type = event['type']
            events[type].append(event)

        return events

    def parse(self, events):
        """
        Parse events from the RTM stream.

        Arguments:
            events (defaultdict): Events to parse.
        """
        messages = events['message']

        for message in messages:
            logger.info(f'Parsing message [{message}].')

            text = message['text']
            if self.id in text:
                text = text.lower()
                timestamp = message['ts']

                logger.info(f'Message at [{timestamp}] contains bot ID [{self.id}].')

                for action, triggers in self.actions.items():
                    if any(trigger.lower() in text for trigger in triggers):
                        logger.info(f'Triggering the [{action}] action.')

                        getattr(self, action)(message)
                        break
                else:
                    logger.info(f'Message at [{timestamp}] does not include any triggers.')

    def health(self, message):
        """
        Post a health message.

        Arguments:
            message (dict): Message mentioning the bot which includes a 'health' trigger.
        """
        user = self.users[message['user']]
        self.post(message['channel'], f'@{user} I\'m here!')

    def help(self, message):
        """
        Post a message explaining how to use the bot.

        Arguments:
            message (dict): Message mentioning the bot which includes a 'help' trigger.
        """
        user = self.users[message['user']]

        lines = []
        for action, triggers in self.actions.items():
            docstring = [line.strip() for line in getattr(self, action).__doc__.split('\n') if line]

            triggers = [f'`{trigger}`' for trigger in triggers]
            words = conversational_join(triggers, conjunction='or')

            lines.append(
                f'*{action}*: {docstring[0]} Trigger by including {words} in your message.'
            )

        help_message = '\n'.join(lines)
        self.post(message['channel'],  f'@{user} here\'s what I can do.\n\n{help_message}')

    def show(self, message):
        """
        Post a message showing court availability. Include `tomorrow` in your message to look tomorrow.

        Arguments:
            message (dict): Message mentioning the bot which includes a 'show' trigger.
        """
        user = self.users[message['user']]
        text = message['text'].lower()

        tomorrow = 'tomorrow' in text
        when = 'tomorrow' if tomorrow else 'today'

        match = re.search(r'#(?P<number>\d)', text)
        number = int(match.group('number')) if match else None

        if number and not constants.COURTS.get(number):
            self.post(message['channel'], f'@{user} #{number} isn\'t a Z-Center court number.')

        self.post(message['channel'], f'@{user} hold on, let me take a look.')
        try:
            data = self.spider.availability(number=number, tomorrow=tomorrow)
        except:
            logger.error('Failed to retrieve court availability data.')

            self.post(message['channel'], f'@{user} something went wrong. Sorry!')

        lines = []
        for court, hours in data.items():
            if hours:
                formatted_hours = [constants.HOURS[hour] for hour in hours]
                times = conversational_join(formatted_hours)

                lines.append(f'#{court} is available {when} at {times}.')

        if number:
            if lines:
                self.post(message['channel'], f'@{user} {lines[0]}')
            else:
                self.post(message['channel'], f'@{user} #{number} is not available {when}.')
        else:
            if lines:
                availability_message = '\n'.join(lines)
                self.post(
                    message['channel'],
                    f'@{user} here\'s how the courts look:\n\n{availability_message}'
                )
            else:
                self.post(
                    message['channel'],
                    f'@{user} there are no courts available {when}.'
                )

    def book(self, message):
        """
        Book a court.

        Arguments:
            message (dict): Message mentioning the bot which includes a 'book' trigger.
        """
        user = self.users[message['user']]
        self.post(message['channel'], f'@{user} sorry, I can\'t book courts yet.')

    def post(self, channel, text):
        """
        Post text to the given channel.

        See https://api.slack.com/methods/chat.postMessage.

        Arguments:
            channel (str): The channel to which to post.
            text (str): The message to post.
        """
        self.client.api_call(
            'chat.postMessage',
            as_user=True,
            channel=channel,
            link_names=True,
            text=text,
        )
