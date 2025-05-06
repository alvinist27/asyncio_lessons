import logging
from asyncio import StreamReader, StreamWriter

logger = logging.getLogger('base')


async def write_message(message: str, writer: StreamWriter) -> None:
    writer.write(message.encode())
    await writer.drain()
    logger.info(f'Sent: {message}')


async def read_message(reader: StreamReader) -> str:
    message = await reader.readline()
    decoded_message = message.decode()
    logger.info(f'Received: {decoded_message!r}')
    return decoded_message
