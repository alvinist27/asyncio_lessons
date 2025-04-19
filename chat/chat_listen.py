import argparse
import asyncio
import logging
import os
from datetime import datetime

import aiofiles
from dotenv import load_dotenv

from chat.config_data import ConfigData

load_dotenv()
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


async def listen_chat(config_data):
    reader, writer = await asyncio.open_connection(config_data.host, config_data.port)
    async with aiofiles.open(config_data.history_file_path, mode='a') as history_file:
        while data := await reader.read(1000):
            current_datetime = datetime.now().strftime("%d.%m.%Y %H:%M")
            try:
                await history_file.write(data.decode())
            except UnicodeDecodeError:
                writer.close()
                await writer.wait_closed()
                logging.info(f'{current_datetime}: UnicodeDecodeError')
            else:
                logging.info(f'{current_datetime}: {data.decode()}')


def configure_application() -> ConfigData:
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='set connection host')
    parser.add_argument('--port', help='set connection port')
    parser.add_argument('--history', help='set path to log file')
    parser_args = parser.parse_args()
    return ConfigData(
        host=parser_args.host or os.getenv('LISTEN_HOST', ''),
        port=parser_args.port or os.getenv('LISTEN_PORT', ''),
        history_file_path=parser_args.history or os.getenv('HISTORY_FILE_NAME', ''),
    )


if __name__ == '__main__':
    asyncio.run(listen_chat(configure_application()))
