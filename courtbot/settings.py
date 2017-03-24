import os


SLACK_RTM_READ_DELAY = int(os.environ.get('SLACK_RTM_READ_DELAY', 1))
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SLACK_USERNAME = os.environ.get('SLACK_USERNAME', 'courtbot')
