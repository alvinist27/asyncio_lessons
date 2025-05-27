import logging
from functools import wraps
from time import sleep

from trio_websocket import ConnectionClosed, HandshakeError

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def relaunch_on_disconnect(async_function):
    @wraps(async_function)
    async def wrapper(*args, **kwargs):
        while True:
            try:
                return await async_function(*args, **kwargs)
            except (ConnectionClosed, HandshakeError) as exc:
                logger.error(f'exc={exc}')
            sleep(1)
    return wrapper
