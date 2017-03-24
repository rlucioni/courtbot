import datetime
import json
import logging
from time import sleep

import dryscrape
import requests

from courtbot import constants, settings
from courtbot.exceptions import AvailabilityError


logger = logging.getLogger(__name__)


class Spider:
    """
    Spider for accessing MIT Recreation's scheduling system.
    """
    def __init__(self):
        logger.info('Initializing spider.')

        self.base_url = 'https://east-a-60ols.csi-cloudapp.net'

        dryscrape.start_xvfb()
        self.session = dryscrape.Session(base_url=self.base_url)

        # No need to load images.
        self.session.set_attribute('auto_load_images', False)

    def login(self):
        """Log in to MIT Recreation."""
        logger.info('Attempting to log in to MIT Recreation.')

        login_path = '/MIT/Login.aspx'
        self.session.visit(login_path)

        username_input = '#ctl00_pageContentHolder_loginControl_UserName'
        password_input = '#ctl00_pageContentHolder_loginControl_Password'
        login_button = '#ctl00_pageContentHolder_loginControl_Login'

        self.session.at_css(username_input).set(settings.DAPER_USERNAME)
        self.session.at_css(password_input).set(settings.DAPER_PASSWORD)
        self.session.at_css(login_button).click()

        # It seems to take some time for dryscrape session cookies to be set.
        # This pause ensures that cookies required for accessing the scheduling
        # API are present.
        sleep(1)

        # TODO: Cache cookies with https://pypi.python.org/pypi/cachetools to avoid
        # unnecessary logins.
        logger.info('Logged in to MIT Recreation.')

    def availability(self, number=None, tomorrow=False):
        """
        Retrieve court availability data.

        You must log in to MIT Recreation before calling this method.

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
        resource_ids = [constants.COURTS[number]] if number else constants.RESOURCES.keys()

        day = datetime.datetime.now()
        if tomorrow:
            day += datetime.timedelta(days=1)

        date_string = day.strftime('%m/%d/%Y')

        url = self.base_url + '/MIT/Library/OlsService.asmx/GetSchedulerResourceAvailability'

        # Cookies returned by dryscrape are strings that look like the following:
        # 'AspxAutoDetectCookieSupport=1; domain=east-a-60ols.csi-cloudapp.net; path=/'
        cookies = [cookie.split(';')[0].split('=') for cookie in self.session.cookies()]
        cookies = {name: value for name, value in cookies}

        data = {
            'siteId': '1261',
            'resourceIds': [str(resource_id) for resource_id in resource_ids],
            'selectedDate': date_string
        }
        # Specify separators with no trailing whitespace for compact encoding.
        data = json.dumps(data, separators=(',', ':'))

        logger.info(f'Requesting court availability data for {date_string}.')
        response = requests.post(url, headers=settings.REQUEST_HEADERS, cookies=cookies, data=data)

        if response.status_code != 200:
            raise AvailabilityError

        logger.info('Successfully retrieved court availability data.')
        courts = response.json()['d']['Value']

        hours = {}
        for court in courts:
            resource_id = court['Id']
            number = constants.RESOURCES[resource_id]

            hours[number] = self.hourly(court['Availability'], tomorrow)

        return hours

    def hourly(self, minutes, tomorrow):
        """
        Convert raw availability data to an array of available hours.

        The API represent's a court's availability as follows:

        {
            'Id': 17,
            'Availability': [
                {
                    'IsAvailable': False,
                    'TimeId': 0,
                },
                {
                    'IsAvailable': False,
                    'TimeId': 1,
                },
                ...
                {
                    'IsAvailable': False,
                    'TimeId': 1439,
                }
            ]
        }

        Arguments:
            minutes (list): The 'Availability' list, an example of which is above.
            tomorrow (bool): Whether or not these times are for tomorrow.

        Returns:
            list: Hours during which the court is available.
        """
        hours = []
        now = datetime.datetime.now()

        for minute in minutes:
            if minute['TimeId'] in constants.TOP_OF_HOUR and minute['IsAvailable']:
                hour = minute['TimeId'] // 60

                if tomorrow or hour > now.hour:
                    hours.append(hour)

        return hours

    def book(self, number):
        """
        Book a court.

        Arguments:
            number (int): The (Z-Center) court number to book.
        """
        # TODO: Check availability before attempting to book.
        raise NotImplementedError('Booking is not supported yet.')

        # This cURL command (with headers added) POSTs appears to stage a reservation,
        # but doesn't complete it. Clicking through the booking process might be
        # easier than dealing with the form submit required to complete the booking.
        # curl 'https://east-a-60ols.csi-cloudapp.net/MIT/Library/OlsService.asmx/SetScheduleInformation' \
        # --data-binary $'{scheduleInformation:\'{"ScheduleDate":"03/26/2017","Duration":60,"Resource":"Zesiger \
        # Squash Court #1","Provider":"","SiteId":"1261","ProviderId":0,"ResourceId":"17","ServiceId":4,\
        # "ServiceName":"Recreational Squash","ServiceUniqueIdentifier":"757170ab-4338-4ff6-868d-2fb51cc449f8"}\', \
        # startTime:\'540\'}'

        # scheduler_path = (
        #     '/MIT/Members/Scheduler/BookSchedule.aspx?'
        #     'siteid=1261&'
        #     'catid=fe02d8bf-d476-4738-aabe-d5b4c9df7d61&'
        #     'provid=0&'
        #     'serviceid=757170ab-4338-4ff6-868d-2fb51cc449f8&'
        #     f'd={day_string}&'
        #     'du=60'
        # )

        # self.session.visit(scheduler_path)

        # court_listing = session.at_css('#ctl00_pageContentHolder_lstResource')

        # courts = court_listing.xpath('option')
        # for court in courts:
        #     if 'zesiger' in court.text().lower():
        #         court.select_option()

        # select_all_id = '#ancSchSelectAll'
        # session.at_css(select_all_id).click()

        # # This element seems to overlap with the search button and prevents it from being clicked.
        # problem_element_id = 'progressDialog_backgroundElement'
        # js = (
        #     f'var element = document.getElementById("{problem_element_id}");'
        #     'element.parentNode.removeChild(element);'
        # )
        # session.exec_script(js)

        # search_id = '#ancSchSearch'
        # session.at_css(search_id).click()
