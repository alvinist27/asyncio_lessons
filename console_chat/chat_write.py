import argparse
import asyncio
import json
import logging
import os
from asyncio import StreamReader, StreamWriter

import aiofiles
from dotenv import load_dotenv

from console_chat.config_data import ConfigData
from console_chat.connections import open_connection

AUTH_ERROR_MESSAGE = 'Authentication error!'
TOKEN_ERROR_MESSAGE = 'Unknown token. Check it or register again.'
REGISTRATION_ERROR_MESSAGE = 'Registration error!'
USER_HASH_FILE_NAME = 'user_hash.txt'

load_dotenv()
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def configure_application() -> ConfigData:
    parser = argparse.ArgumentParser()
    parser.add_argument('message', help='set message for sending')
    parser.add_argument('-s', '--host', help='set connection host')
    parser.add_argument('-p', '--port', help='set connection port')
    parser.add_argument('-t', '--token', help='set user auth token')
    parser.add_argument('-u', '--username', help='set username')
    parser_args = parser.parse_args()
    return ConfigData(
        host=parser_args.host or os.getenv('WRITE_HOST', ''),
        port=parser_args.port or os.getenv('WRITE_PORT', ''),
        message=sanitize(parser_args.message or os.getenv('WRITE_MESSAGE', '')),
        token=parser_args.token or os.getenv('WRITE_TOKEN', ''),
        username=sanitize(parser_args.username or os.getenv('WRITE_USERNAME', '')),
    )


def sanitize(message: str) -> str:
    return message.replace('\n', ' ')


async def write_message(message: str, writer: StreamWriter) -> None:
    writer.write(message.encode())
    await writer.drain()
    logging.info(f'Sent: {message}')


async def read_message(reader: StreamReader) -> str:
    message = await reader.readline()
    decoded_message = message.decode()
    logging.info(f'Received: {decoded_message!r}')
    return decoded_message


async def register(config_data: ConfigData, reader: StreamReader, writer: StreamWriter) -> None:
    logging.info('Started user registration')
    await read_message(reader=reader)
    await write_message(message='\n', writer=writer)
    await read_message(reader=reader)
    await write_message(message=f'{config_data.username}\n', writer=writer)
    auth_token_data = await read_message(reader=reader)
    try:
        json_message = json.loads(auth_token_data)
    except json.JSONDecodeError:
        logging.error(REGISTRATION_ERROR_MESSAGE)
        raise
    async with aiofiles.open(USER_HASH_FILE_NAME, mode='w') as hash_file:
        await hash_file.write(json_message['account_hash'])


async def authorise(reader: StreamReader, writer: StreamWriter) -> None:
    await read_message(reader=reader)
    async with aiofiles.open(USER_HASH_FILE_NAME, mode='r') as hash_file:
        token = await hash_file.read()
    await write_message(message=f'{token}\n', writer=writer)
    auth_token_data = await read_message(reader=reader)
    try:
        json_message = json.loads(auth_token_data)
    except json.JSONDecodeError:
        logging.error(AUTH_ERROR_MESSAGE)
        raise
    else:
        if json_message is None:
            logging.error(TOKEN_ERROR_MESSAGE)
            raise ValueError(TOKEN_ERROR_MESSAGE)


async def main() -> None:
    config_data = configure_application()
    async with open_connection(host=config_data.host, port=config_data.port) as (reader, writer):
        await register(config_data=config_data, reader=reader, writer=writer)
    async with open_connection(host=config_data.host, port=config_data.port) as (reader, writer):
        await authorise(reader=reader, writer=writer)
        await write_message(message=config_data.message, writer=writer)


if __name__ == '__main__':
    asyncio.run(main())
