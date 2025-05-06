import asyncio
from contextlib import asynccontextmanager


@asynccontextmanager
async def open_connection(host, port):
    writer = None
    try:
        reader, writer = await asyncio.open_connection(host, port)
        yield reader, writer
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()
