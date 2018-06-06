import logging
from logging.config import dictConfig

import boto3


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
    },
})

logger = logging.getLogger(__name__)

FUNCTION_NAME = 'courtbot-prod'
KEEP_COUNT = 2


def prune():
    # https://boto3.readthedocs.io/en/latest/reference/services/lambda.html
    client = boto3.client('lambda')

    response = client.list_versions_by_function(FunctionName=FUNCTION_NAME)
    qualifiers = [version['Version'] for version in response['Versions']]
    versions = [int(q) for q in qualifiers if q != '$LATEST']
    versions = sorted(versions, reverse=True)
    to_delete = versions[KEEP_COUNT:]

    logger.info(
        f'found {FUNCTION_NAME} versions {versions}, will delete {to_delete}'
    )

    for version in to_delete:
        logger.info(f'deleting version {version}')
        client.delete_function(
            FunctionName=FUNCTION_NAME,
            Qualifier=str(version),
        )


if __name__ == '__main__':
    prune()
