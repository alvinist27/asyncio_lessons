import argparse
import asyncio
import json
import logging
import os

import aiofiles
from dotenv import load_dotenv

from chat.config_data import ConfigData

load_dotenv()
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


class Chat:
    @staticmethod
    def configure_application() -> ConfigData:
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', help='set connection host')
        parser.add_argument('--port', help='set connection port')
        parser_args = parser.parse_args()
        return ConfigData(
            host=parser_args.host or os.getenv('WRITE_HOST', ''),
            port=parser_args.port or os.getenv('WRITE_PORT', ''),
        )

    @staticmethod
    async def register(config_data: ConfigData) -> None:
        logging.info('Started user registration')
        reader, writer = await asyncio.open_connection(config_data.host, config_data.port)

        data = await reader.readline()
        logging.info(f'Received: {data.decode()!r}')

        message = '\n'
        writer.write(message.encode())
        await writer.drain()
        logging.info(f'Sent: {message}')

        data = await reader.readline()
        logging.info(f'Received: {data.decode()!r}')

        message = 'alvin'
        writer.write(f'{message}\n'.encode())
        await writer.drain()
        logging.info(f'Sent: {message}')

        data = await reader.readline()
        logging.info(f'Received: {data.decode()!r}')
        try:
            json_message = json.loads(data)
        except json.JSONDecodeError:
            logging.info('Registration error!')
            raise
        finally:
            writer.close()
            await writer.wait_closed()
        async with aiofiles.open('user_hash.txt', mode='w') as hash_file:
            await hash_file.write(json_message['account_hash'])

    @staticmethod
    async def _login(config_data: ConfigData) -> tuple:
        reader, writer = await asyncio.open_connection(config_data.host, config_data.port)
        data = await reader.read(100)
        logging.info(f'Received: {data.decode()!r}')
        async with aiofiles.open('user_hash.txt', mode='r') as hash_file:
            token = await hash_file.read()
        writer.write(f'{token}\n'.encode())
        await writer.drain()
        logging.info(f'Sent: {token}')
        data = await reader.readline()
        logging.info(f'Received: {data.decode()!r}')
        try:
            json_message = json.loads(data)
        except json.JSONDecodeError:
            pass
        else:
            if json_message is None:
                logging.error('Unknown token. Check it or register again.')
                return None, None
        return reader, writer

    @classmethod
    async def authorise(cls, config_data: ConfigData):
        _, writer = await cls._login(config_data)
        if not writer:
            return
        writer.close()
        await writer.wait_closed()

    @classmethod
    async def send_message(cls, config_data: ConfigData, message: str) -> None:
        _, writer = await cls._login(config_data)
        if not writer:
            return
        writer.write(f'{message}\n'.encode())
        logging.info(f'Sent: {message}')
        writer.close()
        await writer.wait_closed()

    @classmethod
    async def start(cls) -> None:
        config_data = cls.configure_application()
        await cls.register(config_data=config_data)
        await cls.send_message(config_data=config_data, message='message')


if __name__ == '__main__':
    asyncio.run(Chat.start())
