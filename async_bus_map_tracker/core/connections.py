import logging
from functools import wraps

from trio import sleep
from trio_websocket import ConnectionClosed, HandshakeError

from async_bus_map_tracker.core import consts

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def relaunch_on_disconnect(async_function):
    @wraps(async_function)
    async def wrapper(*args, **kwargs):
        while True:
            try:
                return await async_function(*args, **kwargs)
            except (ConnectionClosed, HandshakeError) as exc:
                logger.error(f'Exception occurred exc={exc}. Reconnect in {consts.RECONNECT_TIMEOUT} seconds')
            await sleep(consts.RECONNECT_TIMEOUT)
    return wrapper
