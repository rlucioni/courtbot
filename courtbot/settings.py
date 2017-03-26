import os


CACHE_TTL = int(os.environ.get('CACHE_TTL', 3600))

DAPER_USERNAME = os.environ.get('DAPER_USERNAME')
DAPER_PASSWORD = os.environ.get('DAPER_PASSWORD')

GITHUB_LINK = os.environ.get('GITHUB_LINK', 'https://github.com/rlucioni/courtbot')

REQUEST_HEADERS = {
    'Pragma': 'no-cache',
    'Origin': 'https://east-a-60ols.csi-cloudapp.net',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/56.0.2924.87 Safari/537.36'
    ),
    'Content-Type': 'application/json; charset=UTF-8',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Cache-Control': 'no-cache',
    'X-Requested-With': 'XMLHttpRequest',
}

SLACK_HANDLE = os.environ.get('SLACK_HANDLE', 'courtbot')
SLACK_RTM_READ_DELAY = int(os.environ.get('SLACK_RTM_READ_DELAY', 1))
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
