import json
import logging
import operator

import requests
from cachetools import cachedmethod, TTLCache
from selenium import webdriver

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

        options = webdriver.ChromeOptions()
        options.binary_location = '/usr/bin/google-chrome-stable'
        options.add_argument('headless')
        # https://developers.google.com/web/updates/2017/04/headless-chrome#faq
        options.add_argument('disable-gpu')
        options.add_argument('window-size=1200x600')

        self.driver = webdriver.Chrome(chrome_options=options)
        self.driver.implicitly_wait(10)

        self.base_url = 'https://east-a-60ols.csi-cloudapp.net'

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
        self.driver.get(self.base_url + login_path)

        username_id = 'ctl00_pageContentHolder_loginControl_UserName'
        password_id = 'ctl00_pageContentHolder_loginControl_Password'

        # Headless Chrome still requires Xvfb for send_key interactions. A temporary
        # workaround is to use JavaScript to fill form fields instead of send_keys.
        # This is a known issue tracked by https://bugs.chromium.org/p/chromedriver/issues/detail?id=1772.
        self.driver.execute_script(f'document.getElementById("{username_id}").value = "{settings.DAPER_USERNAME}";')
        self.driver.execute_script(f'document.getElementById("{password_id}").value = "{settings.DAPER_PASSWORD}";')

        login_button = self.driver.find_element_by_css_selector('#ctl00_pageContentHolder_loginControl_Login')
        login_button.click()

        # Verify that login succeeded by waiting for this element to appear.
        self.driver.find_element_by_css_selector('#menu_SCH')

        return {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

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
        self.driver.get(self.base_url + confirm_path)

        confirm_button = self.driver.find_element_by_css_selector('#ctl00_pageContentHolder_btnContinueCart')
        confirm_button.click()

        # Verify that booking succeeded by waiting for a unique element to appear
        # on the booking confirmation/receipt page.
        self.driver.find_element_by_css_selector('#ctl00_pageContentHolder_lblThankYou')
