#!/usr/bin/env python
import logging

from courtbot.bot import Bot


logger = logging.getLogger(__name__)


if __name__ == '__main__':
    logging.basicConfig(
        style='{',
        format='{asctime} {levelname} {process} [{filename}:{lineno}] - {message}',
        level=logging.INFO
    )

    Bot().connect()
