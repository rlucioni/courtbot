import json
import logging
import operator

from cachetools import cachedmethod, TTLCache
import dryscrape
import requests

from courtbot import constants, settings
from courtbot.exceptions import AvailabilityError, BookingError
from courtbot.utils import hourly, slash_separated_date


logger = logging.getLogger(__name__)


class Spider:
    """
    Spider for accessing MIT Recreation's scheduling system.
    """
    def __init__(self):
        logger.info('Initializing spider.')

        dryscrape.start_xvfb()
        self.base_url = 'https://east-a-60ols.csi-cloudapp.net'
        self.session = dryscrape.Session(base_url=self.base_url)

        # No need to load images.
        self.session.set_attribute('auto_load_images', False)

        # LRU performs best when maxsize is a power of two.
        maxsize = 2 ** 5
        self.cache = TTLCache(maxsize, settings.CACHE_TTL)

    @cachedmethod(operator.attrgetter('cache'))
    def login(self):
        """Log in to MIT Recreation.

        Returns:
            dict: Cookies set after logging in, ready for use with requests.
        """
        logger.info('Logging in to MIT Recreation.')

        login_path = '/MIT/Login.aspx'
        self.session.visit(login_path)

        username_input = '#ctl00_pageContentHolder_loginControl_UserName'
        password_input = '#ctl00_pageContentHolder_loginControl_Password'
        login_button = '#ctl00_pageContentHolder_loginControl_Login'

        self.session.at_css(username_input).set(settings.DAPER_USERNAME)
        self.session.at_css(password_input).set(settings.DAPER_PASSWORD)
        self.session.at_css(login_button).click()

        self.session.wait_for(lambda: self.session.at_css('#menu_SCH'))

        # Cookies returned by dryscrape are strings that look like the following:
        # 'AspxAutoDetectCookieSupport=1; domain=east-a-60ols.csi-cloudapp.net; path=/'
        cookies = [cookie.split(';')[0].split('=') for cookie in self.session.cookies()]
        cookies = {name: value for name, value in cookies}

        return cookies

    def availability(self, number=None, tomorrow=False):
        """
        Retrieve court availability data.

        Data comes from the same API used by the scheduling application. Courts
        can only be booked by the hour, but the API returns minute-by-minute
        court availability.

        ಠ_ಠ

        Keyword Arguments:
            number (int): The Z-Center court number for which to check availability.
                DuPont courts are not supported; they're almost never available.

            tomorrow (bool): Whether to look at court availability for tomorrow
                instead of today. The court reservation system only allows booking
                one day in advance.

        Raises:
            AvailabilityError: If there's a problem retrieving data from the API.

        Returns:
            dict: Lists indicating court availability, keyed by court number.
        """
        date_string = slash_separated_date(tomorrow)
        logger.info(f'Requesting court availability data for {date_string}.')

        resource_ids = [constants.COURTS[number]] if number else constants.RESOURCES.keys()
        data = {
            'siteId': '1261',
            'resourceIds': [str(resource_id) for resource_id in resource_ids],
            'selectedDate': date_string,
        }

        url = self.base_url + '/MIT/Library/OlsService.asmx/GetSchedulerResourceAvailability'
        response = requests.post(url, headers=settings.REQUEST_HEADERS, json=data)

        if response.status_code != 200:
            raise AvailabilityError

        hours = {}
        courts = response.json()['d']['Value']

        for court in courts:
            resource_id = court['Id']
            number = constants.RESOURCES[resource_id]

            hours[number] = hourly(court['Availability'], tomorrow)

        return hours

    def book(self, number, hour, tomorrow=False):
        """
        Book a court.

        Arguments:
            number (int): The (Z-Center) court number to book.
            hour (int): The (ISO 8601) hour for which to book.

        Keyword Arguments:
            tomorrow (bool): Whether to book a court for tomorrow instead of today.
                The court reservation system only allows booking one day in advance.

        Raises:
            AvailabilityError: If the court is not available at the requested hour.
            BookingError: If creation of a new booking fails.
        """
        date_string = slash_separated_date(tomorrow)
        hour_string = constants.HOURS[hour]
        logger.info(f'Attempting to book court #{number} at {hour_string} on {date_string}.')

        availability = self.availability(number=number, tomorrow=tomorrow)
        if hour not in availability[number]:
            raise AvailabilityError

        cookies = self.login()
        logger.info(f'Cookies present: {cookies}')

        schedule_data = {
            'ScheduleDate': date_string,
            'Duration': 60,
            'Resource': f'Zesiger Squash Court #{number}',
            'Provider': '',
            'SiteId': 1261,
            'ProviderId': 0,
            # This resource ID must be a string. Don't ask me why.
            'ResourceId': str(constants.COURTS[number]),
            'ServiceId': 4,
            'ServiceName': 'Recreational Squash',
            'ServiceUniqueIdentifier': '757170ab-4338-4ff6-868d-2fb51cc449f8',
        }

        data = {
            # The values for both of these keys need to be strings. (╯ಠ_ಠ）╯︵ ┻━┻
            'scheduleInformation': json.dumps(schedule_data, separators=(',', ':')),
            'startTime': str(hour * 60),
        }

        # Specify separators with no trailing whitespace for compact encoding.
        data = json.dumps(data, separators=(',', ':'))

        # This request "stages" a reservation, but doesn't complete it. Clicking
        # through the booking process from this point is easier than dealing with
        # the crazy ASP.NET form submit required to complete the booking.
        url = self.base_url + '/MIT/Library/OlsService.asmx/SetScheduleInformation'
        response = requests.post(url, headers=settings.REQUEST_HEADERS, cookies=cookies, data=data)

        if response.status_code != 200:
            raise BookingError

        confirm_path = '/MIT/Members/Scheduler/AddFamilyMembersScheduler.aspx'
        self.session.visit(confirm_path)

        confirm_button = '#ctl00_pageContentHolder_btnContinueCart'
        self.session.wait_for(lambda: self.session.at_css(confirm_button))
        self.session.at_css(confirm_button).click()
