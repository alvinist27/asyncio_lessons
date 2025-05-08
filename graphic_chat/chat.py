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
from async_timeout import timeout
from dotenv import load_dotenv
from exceptiongroup import ExceptionGroup

from graphic_chat import choices, consts
from graphic_chat.config_data import ConfigData
from graphic_chat.connections import open_connection, reconnect
from graphic_chat.exceptions import TkAppClosed
from graphic_chat.gui import draw, set_connection_status
from graphic_chat.messages import is_bot_message, read_message, write_message
from graphic_chat.chat_types import QueuesType

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


async def watch_for_connection(queue: asyncio.Queue) -> None:
    while message := await queue.get():
        current_timestamp = int(time.time())
        watchdog_logger.info(f'[{current_timestamp}] {message}')


async def ping_pong(reader: StreamReader, writer: StreamWriter, queues: QueuesType) -> None:
    set_connection_status(
        queues[choices.QueueNames.STATUS_UPDATES],
        choices.ReadConnectionStateChanged.INITIATED,
        choices.SendingConnectionStateChanged.INITIATED,
    )
    while True:
        try:
            async with timeout(consts.BASE_TIMEOUT) as timeout_obj:
                await reader.readline()
                await write_message(consts.SUBMIT_MESSAGE_CHARS, writer)
        finally:
            if timeout_obj.expired:
                set_connection_status(
                    queues[choices.QueueNames.STATUS_UPDATES],
                    choices.ReadConnectionStateChanged.CLOSED,
                    choices.SendingConnectionStateChanged.CLOSED,
                )
                queues[choices.QueueNames.WATCHDOG].put_nowait(consts.PING_PONG_CONNECTION_ERROR_MESSAGE)
                await asyncio.sleep(consts.PING_PONG_ERROR_RECONNECT_TIMEOUT)
            else:
                set_connection_status(
                    queues[choices.QueueNames.STATUS_UPDATES],
                    choices.ReadConnectionStateChanged.ESTABLISHED,
                    choices.SendingConnectionStateChanged.ESTABLISHED,
                )
                await asyncio.sleep(consts.PING_PONG_RECONNECT_TIMEOUT)


async def write_chat_messages(writer: StreamWriter, queues: QueuesType) -> None:
    while message := await queues[choices.QueueNames.SENDING_MESSAGES].get():
        await write_message(message=f'{message}{consts.SUBMIT_MESSAGE_CHARS}', writer=writer)
        queues[choices.QueueNames.WATCHDOG].put_nowait(consts.WRITE_SUCCESS_MESSAGE)


async def read_chat_messages(host: str, port: str, queues: QueuesType) -> None:
    async with open_connection(host=host, port=port) as (reader, writer):
        while data := await reader.readline():
            message: str = data.decode()
            if is_bot_message(message=message):
                continue
            queues[choices.QueueNames.WATCHDOG].put_nowait(consts.READ_SUCCESS_MESSAGE)
            queues[choices.QueueNames.MESSAGES].put_nowait(message)
            queues[choices.QueueNames.MESSAGES_TO_SAVE].put_nowait(message)


async def preload_chat_history(messages_queue: asyncio.Queue) -> None:
    async with aiofiles.open(consts.CHAT_HISTORY_FILE_NAME, 'r') as history_file:
        while data := await history_file.readline():
            messages_queue.put_nowait(data)
        messages_queue.put_nowait(f'{consts.LATEST_MESSAGES_LABEL}{consts.SUBMIT_MESSAGE_CHARS}')


async def save_messages(messages_to_save_queue: asyncio.Queue) -> None:
    async with aiofiles.open(consts.CHAT_HISTORY_FILE_NAME, 'a') as history_file:
        while True:
            message = await messages_to_save_queue.get()
            await history_file.write(message)


async def authorise(reader: StreamReader, writer: StreamWriter, queues: QueuesType) -> None:
    queues[choices.QueueNames.WATCHDOG].put_nowait(consts.AUTH_START_MESSAGE)
    await read_message(reader=reader)
    async with aiofiles.open(consts.USER_HASH_FILE_NAME, mode='r') as hash_file:
        token = await hash_file.read()
    await write_message(message=f'{token}{consts.SUBMIT_MESSAGE_CHARS}', writer=writer)
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
            queues[choices.QueueNames.STATUS_UPDATES].put_nowait(choices.NicknameReceived(json_message['nickname']))
            queues[choices.QueueNames.WATCHDOG].put_nowait(consts.AUTH_SUCCESS_MESSAGE)
            logger.info(f'Auth successful. User {json_message["nickname"]}')


async def handle_connection(
    write_host: str,
    write_port: str,
    listen_host: str,
    listen_port: str,
    queues: QueuesType,
) -> None:
    while True:
        try:
            async with reconnect(write_host, write_port) as (reader, writer):
                await authorise(reader=reader, writer=writer, queues=queues)
                async with anyio.create_task_group() as task_group:
                    task_group.start_soon(write_chat_messages, writer, queues)
                    task_group.start_soon(ping_pong, reader, writer, queues)
                    task_group.start_soon(read_chat_messages, listen_host, listen_port, queues)
                    task_group.start_soon(watch_for_connection, queues[choices.QueueNames.WATCHDOG])
        except (ConnectionError, ExceptionGroup):
            queues[choices.QueueNames.WATCHDOG].put_nowait(consts.CONNECTION_ERROR_MESSAGE)
            set_connection_status(
                queues[choices.QueueNames.STATUS_UPDATES],
                choices.ReadConnectionStateChanged.CLOSED,
                choices.SendingConnectionStateChanged.CLOSED,
            )
            await asyncio.sleep(consts.BASE_TIMEOUT)
        else:
            set_connection_status(
                queues[choices.QueueNames.STATUS_UPDATES],
                choices.ReadConnectionStateChanged.ESTABLISHED,
                choices.SendingConnectionStateChanged.ESTABLISHED,
            )


async def main() -> None:
    queues: dict[choices.QueueNames, asyncio.Queue] = {
        choices.QueueNames.MESSAGES: asyncio.Queue(),
        choices.QueueNames.MESSAGES_TO_SAVE: asyncio.Queue(),
        choices.QueueNames.SENDING_MESSAGES: asyncio.Queue(),
        choices.QueueNames.STATUS_UPDATES: asyncio.Queue(),
        choices.QueueNames.WATCHDOG: asyncio.Queue(),
    }

    config_data = configure_application()
    await preload_chat_history(queues[choices.QueueNames.MESSAGES])
    async with anyio.create_task_group() as task_group:
        task_group.start_soon(draw, queues)
        task_group.start_soon(save_messages, queues[choices.QueueNames.MESSAGES_TO_SAVE])
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
