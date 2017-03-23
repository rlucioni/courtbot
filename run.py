#!/usr/bin/env python
import logging


logger = logging.getLogger(__name__)


if __name__ == '__main__':
    logging.basicConfig(
        style='{',
        format='{asctime} {levelname} {process} [{filename}:{lineno}] - {message}',
        level=logging.INFO
    )

    logger.info('Bot initialized.')

    while True:
        pass
