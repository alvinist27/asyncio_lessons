import logging
from asyncio import StreamReader, StreamWriter

from graphic_chat import consts

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


def is_bot_message(message: str):
    username = message[:message.find(consts.MESSAGE_USERNAME_SPLIT_CHAR)]
    return len(username.split()) == consts.BOT_USERNAME_WORDS_COUNT
