from collections import defaultdict
import logging
from time import sleep

from slackclient import SlackClient
from slackclient._server import SlackConnectionError

from courtbot import settings


logger = logging.getLogger(__name__)


class Bot:
    """
    Bot class for reading from and writing to Slack.

    Uses Slack's RTM API. For more about the RTM API, see documentation at
    http://slackapi.github.io/python-slackclient/real_time_messaging.html.
    """
    def __init__(self):
        logger.info('Initializing courtbot.')

        self.client = SlackClient(settings.SLACK_TOKEN)

        # Find and cache the bot's user ID. The ID is used to identify messages
        # which mention the bot.
        users = self.client.api_call('users.list')['members']
        for user in users:
            if user['name'] == settings.SLACK_USERNAME:
                self.bot_id = user['id']

                logger.info(f'Bot ID is [{self.bot_id}].')

        self.actions = {
            'help': ['help'],
            'show': ['show', 'availab', 'look'],
            'book': ['book', 'reserve'],
        }

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
            if self.bot_id in text:
                text = text.lower()
                timestamp = message['ts']

                logger.info(f'Message at [{timestamp}] contains bot ID [{self.bot_id}].')

                for action, triggers in self.actions.items():
                    if any(trigger.lower() in text for trigger in triggers):
                        logger.info(f'Triggering the [{action}] action.')

                        getattr(self, action)(message)
                        break
                else:
                    logger.info(f'Message at [{timestamp}] does not include any triggers.')

    def help(self, message):
        """
        Post a message explaining how to use the bot.

        Arguments:
            message (dict): Message mentioning the bot which includes a 'help' trigger.
        """
        self.post(message['channel'], 'This is a help message.')

    def show(self, message):
        """
        Post a message showing court availability.

        Arguments:
            message (dict): Message mentioning the bot which includes a 'show' trigger.
        """
        self.post(message['channel'], 'This is a court availability message.')

    def book(self, message):
        """
        Book a court.

        Arguments:
            message (dict): Message mentioning the bot which includes a 'book' trigger.
        """
        self.post(message['channel'], 'This is a booking message.')

    def post(self, channel, text):
        """
        Post text to the given channel.

        Arguments:
            channel (str): The channel to which to post.
            text (str): The message to post.
        """
        self.client.api_call(
            'chat.postMessage',
            as_user=True,
            channel=channel,
            text=text
        )
