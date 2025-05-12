import logging
import time
from contextlib import contextmanager

logger = logging.getLogger('root')
logging.basicConfig(level=logging.INFO)


@contextmanager
def count_time():
    start_time = time.monotonic()
    try:
        yield time.monotonic() - start_time
    finally:
        logger.info(f'Анализ закончен за {round(time.monotonic() - start_time, 4)} сек')
