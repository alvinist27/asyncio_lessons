import asyncio
import socket
from contextlib import asynccontextmanager


@asynccontextmanager
async def open_connection(host, port):
    writer = None
    try:
        reader, writer = await asyncio.open_connection(host, port)
        yield reader, writer
    except (ConnectionError, socket.gaierror, asyncio.TimeoutError, KeyboardInterrupt):
        raise ConnectionError
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()


@asynccontextmanager
async def reconnect(host, port):
    while True:
        async with open_connection(host, port) as (reader, writer):
            yield reader, writer
