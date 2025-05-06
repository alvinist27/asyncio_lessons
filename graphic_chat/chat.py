import argparse
import asyncio
import json
import logging
import os
import time
from asyncio import StreamReader, StreamWriter
from tkinter import messagebox

import aiofiles
import anyio
from anyio import create_task_group
from async_timeout import timeout
from dotenv import load_dotenv
from exceptiongroup import ExceptionGroup

from graphic_chat import choices, consts
from graphic_chat.choices import QueueNames
from graphic_chat.config_data import ConfigData
from graphic_chat.connections import open_connection, reconnect
from graphic_chat.exceptions import TkAppClosed
from graphic_chat.gui import draw
from graphic_chat.messages import read_message, write_message

load_dotenv()
logger = logging.getLogger('base')
watchdog_logger = logging.getLogger('watchdog')
logging.basicConfig(level=logging.INFO)


def configure_application() -> ConfigData:
    parser = argparse.ArgumentParser()
    parser.add_argument('-ls', '--listen_host', help='set listen connection host')
    parser.add_argument('-lp', '--listen_port', help='set listen connection port')
    parser.add_argument('-t', '--token', help='set user auth token')
    parser.add_argument('-ws', '--write_host', help='set write connection host')
    parser.add_argument('-wp', '--write_port', help='set write connection port')
    parser_args = parser.parse_args()
    return ConfigData(
        listen_host=parser_args.listen_host or os.getenv('LISTEN_SERVER_HOST', ''),
        listen_port=parser_args.listen_port or os.getenv('LISTEN_SERVER_PORT', ''),
        user_token=parser_args.token or os.getenv('USER_TOKEN', ''),
        write_host=parser_args.write_host or os.getenv('WRITE_SERVER_HOST', ''),
        write_port=parser_args.write_port or os.getenv('WRITE_SERVER_PORT', ''),
    )


async def watch_for_connection(queue):
    while message := await queue.get():
        current_timestamp = int(time.time())
        watchdog_logger.info(f'[{current_timestamp}] {message}')


async def authorise(reader: StreamReader, writer: StreamWriter, status_updates_queue: asyncio.Queue, watchdog_queue) -> None:
    watchdog_queue.put_nowait('Prompt before auth')
    await read_message(reader=reader)
    async with aiofiles.open(consts.USER_HASH_FILE_NAME, mode='r') as hash_file:
        token = await hash_file.read()
    await write_message(message=f'{token}\n', writer=writer)
    auth_token_data = await read_message(reader=reader)
    try:
        json_message = json.loads(auth_token_data)
    except json.JSONDecodeError:
        logger.error(consts.AUTH_ERROR_MESSAGE)
        raise
    else:
        if json_message is None:
            logger.error(consts.TOKEN_ERROR_MESSAGE)
            messagebox.showerror(title='Неверный токен', message=consts.TOKEN_ERROR_MESSAGE)
        else:
            status_updates_queue.put_nowait(choices.NicknameReceived(json_message['nickname']))
            watchdog_queue.put_nowait('Connection is alive.Authorization done')
            logger.info(f'Выполнена авторизация. Пользователь {json_message["nickname"]}')


async def ping_pong(reader, writer, queues):
    queues[QueueNames.STATUS_UPDATES].put_nowait(choices.ReadConnectionStateChanged.INITIATED)
    queues[QueueNames.STATUS_UPDATES].put_nowait(choices.SendingConnectionStateChanged.INITIATED)
    while True:
        try:
            async with timeout(1) as timeout_obj:
                await reader.readline()
                await write_message('\n\n', writer)
        finally:
            if timeout_obj.expired:
                queues[QueueNames.STATUS_UPDATES].put_nowait(choices.ReadConnectionStateChanged.CLOSED)
                queues[QueueNames.STATUS_UPDATES].put_nowait(choices.SendingConnectionStateChanged.CLOSED)
                queues[QueueNames.WATCHDOG].put_nowait('No connection. 1s timeout is elapsed')
                await asyncio.sleep(5)
            else:
                queues[QueueNames.STATUS_UPDATES].put_nowait(choices.ReadConnectionStateChanged.ESTABLISHED)
                queues[QueueNames.STATUS_UPDATES].put_nowait(choices.SendingConnectionStateChanged.ESTABLISHED)
                await asyncio.sleep(1)


async def write_messages(writer, queues):
    while message := await queues[QueueNames.SENDING].get():
        await write_message(message=f'{message}\n\n\n', writer=writer)
        queues[QueueNames.WATCHDOG].put_nowait('Connection is alive. Message sent')


async def read_msgs(host, port, queues):
    async with open_connection(host=host, port=port) as (reader, writer):
        while data := await reader.readline():
            message = data.decode()
            queues[QueueNames.WATCHDOG].put_nowait('Connection is alive. New message in chat')
            queues[QueueNames.MESSAGES].put_nowait(message)
            queues[QueueNames.MESSAGES_TO_SAVE].put_nowait(message)


async def preload_chat_history(messages_queue: asyncio.Queue):
    async with aiofiles.open(consts.CHAT_HISTORY_FILE_NAME, 'r') as history_file:
        while data := await history_file.readline():
            messages_queue.put_nowait(data)
        messages_queue.put_nowait('==============================latest messages================================\n\n')


async def save_msgs(messages_to_save_queue):
    async with aiofiles.open(consts.CHAT_HISTORY_FILE_NAME, 'a') as history_file:
        while True:
            message = await messages_to_save_queue.get()
            await history_file.write(message)


def handle_connection_error(exception_group: ExceptionGroup) -> None:
    for exc in exception_group.exceptions:
        logger.info(f'Error: {exc}')


async def handle_connection(write_host, write_port, listen_host, listen_port, queues):
    while True:
        try:
            async with reconnect(write_host, write_port) as (reader, writer):
                await authorise(reader=reader, writer=writer, status_updates_queue=queues[QueueNames.STATUS_UPDATES],
                                watchdog_queue=queues[QueueNames.WATCHDOG])
                async with create_task_group() as task_group:
                    task_group.start_soon(write_messages, writer, queues)
                    task_group.start_soon(ping_pong, reader, writer, queues)
                    task_group.start_soon(read_msgs, listen_host, listen_port, queues)
                    task_group.start_soon(watch_for_connection, queues[QueueNames.WATCHDOG])
        except (ConnectionError, ExceptionGroup):
            queues[QueueNames.WATCHDOG].put_nowait('-------------------------ExceptionGroup--------------------------')

            queues[QueueNames.STATUS_UPDATES].put_nowait(choices.ReadConnectionStateChanged.CLOSED)
            queues[QueueNames.STATUS_UPDATES].put_nowait(choices.SendingConnectionStateChanged.CLOSED)
            await asyncio.sleep(1)
        else:
            queues[QueueNames.STATUS_UPDATES].put_nowait(choices.ReadConnectionStateChanged.ESTABLISHED)
            queues[QueueNames.STATUS_UPDATES].put_nowait(choices.SendingConnectionStateChanged.ESTABLISHED)


async def main():
    queues: dict[QueueNames, asyncio.Queue] = {
        QueueNames.MESSAGES: asyncio.Queue(),
        QueueNames.MESSAGES_TO_SAVE: asyncio.Queue(),
        QueueNames.SENDING: asyncio.Queue(),
        QueueNames.STATUS_UPDATES: asyncio.Queue(),
        QueueNames.WATCHDOG: asyncio.Queue(),
    }

    config_data = configure_application()
    await preload_chat_history(queues[QueueNames.MESSAGES])
    async with create_task_group() as task_group:
        task_group.start_soon(draw, queues)
        task_group.start_soon(save_msgs, queues[QueueNames.MESSAGES_TO_SAVE])
        task_group.start_soon(
            handle_connection,
            config_data.write_host,
            config_data.write_port,
            config_data.listen_host,
            config_data.listen_port,
            queues,
        )


if __name__ == '__main__':
    try:
        anyio.run(main)
    except (TkAppClosed, KeyboardInterrupt, ExceptionGroup):
        pass
