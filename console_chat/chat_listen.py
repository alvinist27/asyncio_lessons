import argparse
import asyncio
import logging
import os
from datetime import datetime

import aiofiles
from dotenv import load_dotenv

from console_chat.config_data import ConfigData
from console_chat.connections import open_connection

load_dotenv()
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


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


async def main():
    config_data = configure_application()
    async with open_connection(host=config_data.host, port=config_data.port) as (reader, writer):
        async with aiofiles.open(config_data.history_file_path, mode='a') as history_file:
            while data := await reader.readline():
                current_datetime = datetime.now().strftime("%d.%m.%Y %H:%M")
                await history_file.write(data.decode())
                logger.info(f'{current_datetime}: {data.decode()}')


if __name__ == '__main__':
    asyncio.run(main())
