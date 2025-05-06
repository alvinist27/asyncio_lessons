import argparse
import asyncio
import json
import logging
import os
import time
import tkinter as tk
from asyncio import StreamReader, StreamWriter
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

import aiofiles
import anyio
from anyio import create_task_group
from async_timeout import timeout
from dotenv import load_dotenv
from exceptiongroup import ExceptionGroup

from graphic_chat import consts, statuses
from graphic_chat.config_data import ConfigData
from graphic_chat.connections import open_connection, reconnect
from graphic_chat.exceptions import TkAppClosed

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


def create_status_panel(root_frame):
    status_frame = tk.Frame(root_frame)
    status_frame.pack(side='bottom', fill=tk.X)

    connections_frame = tk.Frame(status_frame)
    connections_frame.pack(side='left')

    nickname_label = tk.Label(connections_frame, height=1, fg='grey', font='arial 10', anchor='w')
    nickname_label.pack(side='top', fill=tk.X)

    status_read_label = tk.Label(connections_frame, height=1, fg='grey', font='arial 10', anchor='w')
    status_read_label.pack(side='top', fill=tk.X)

    status_write_label = tk.Label(connections_frame, height=1, fg='grey', font='arial 10', anchor='w')
    status_write_label.pack(side='top', fill=tk.X)
    return nickname_label, status_read_label, status_write_label


def process_new_message(input_field, sending_queue):
    text = input_field.get()
    sending_queue.put_nowait(text)
    logger.info(f'Пользователь написал: {text}')
    input_field.delete(0, tk.END)


async def update_tk(root_frame, interval=consts.TK_FRAME_UPDATE_INTERVAL):
    while True:
        try:
            root_frame.update()
        except tk.TclError:
            raise TkAppClosed()
        await asyncio.sleep(interval)


async def update_status_panel(status_labels, status_updates_queue):
    nickname_label, read_label, write_label = status_labels

    read_label['text'] = f'Чтение: нет соединения'
    write_label['text'] = f'Отправка: нет соединения'
    nickname_label['text'] = f'Имя пользователя: неизвестно'

    while True:
        msg = await status_updates_queue.get()
        if isinstance(msg, statuses.ReadConnectionStateChanged):
            read_label['text'] = f'Чтение: {msg}'

        if isinstance(msg, statuses.SendingConnectionStateChanged):
            write_label['text'] = f'Отправка: {msg}'

        if isinstance(msg, statuses.NicknameReceived):
            nickname_label['text'] = f'Имя пользователя: {msg.nickname}'


async def update_conversation_history(panel, messages_queue):
    while True:
        msg = await messages_queue.get()

        panel['state'] = 'normal'
        if panel.index('end-1c') != '1.0':
            panel.insert('end', '\n')
        panel.insert('end', msg)
        # TODO сделать промотку умной, чтобы не мешала просматривать историю сообщений
        # ScrolledText.frame
        # ScrolledText.vbar
        panel.yview(tk.END)
        panel['state'] = 'disabled'


async def draw(messages_queue, messages_to_save_queue, sending_queue, status_updates_queue, watchdog_queue):
    root = tk.Tk()

    root.title('Чат Майнкрафтера')

    root_frame = tk.Frame()
    root_frame.pack(fill='both', expand=True)

    status_labels = create_status_panel(root_frame)

    input_frame = tk.Frame(root_frame)
    input_frame.pack(side='bottom', fill=tk.X)

    input_field = tk.Entry(input_frame)
    input_field.pack(side='left', fill=tk.X, expand=True)

    input_field.bind('<Return>', lambda event: process_new_message(input_field, sending_queue))

    send_button = tk.Button(input_frame)
    send_button['text'] = 'Отправить'
    send_button['command'] = lambda: process_new_message(input_field, sending_queue)
    send_button.pack(side='left')

    conversation_panel = ScrolledText(root_frame, wrap='none')
    conversation_panel.pack(side='top', fill='both', expand=True)

    config_data = configure_application()

    await preload_chat_history(messages_queue)
    async with create_task_group() as task_group:
        task_group.start_soon(handle_connection, config_data.write_host, config_data.write_port, config_data.listen_host, config_data.listen_port, sending_queue, messages_queue, messages_to_save_queue, status_updates_queue, watchdog_queue)
        task_group.start_soon(update_tk, root_frame)
        task_group.start_soon(update_status_panel, status_labels, status_updates_queue)
        task_group.start_soon(update_conversation_history, conversation_panel, messages_queue),
        task_group.start_soon(save_msgs, messages_to_save_queue)


async def write_message(message: str, writer: StreamWriter) -> None:
    writer.write(message.encode())
    await writer.drain()
    logging.info(f'Sent: {message}')


async def read_message(reader: StreamReader) -> str:
    message = await reader.readline()
    decoded_message = message.decode()
    logging.info(f'Received: {decoded_message!r}')
    return decoded_message


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
            status_updates_queue.put_nowait(statuses.NicknameReceived(json_message['nickname']))
            watchdog_queue.put_nowait('Connection is alive.Authorization done')
            logger.info(f'Выполнена авторизация. Пользователь {json_message["nickname"]}')


async def ping_pong(reader, writer, status_updates_queue, watchdog_queue):
    status_updates_queue.put_nowait(statuses.ReadConnectionStateChanged.INITIATED)
    status_updates_queue.put_nowait(statuses.SendingConnectionStateChanged.INITIATED)
    while True:
        try:
            async with timeout(1) as timeout_obj:
                await reader.readline()
                await write_message('\n\n', writer)
        finally:
            if timeout_obj.expired:
                status_updates_queue.put_nowait(statuses.ReadConnectionStateChanged.CLOSED)
                status_updates_queue.put_nowait(statuses.SendingConnectionStateChanged.CLOSED)
                watchdog_queue.put_nowait('No connection. 1s timeout is elapsed')
                await asyncio.sleep(5)
            else:
                status_updates_queue.put_nowait(statuses.ReadConnectionStateChanged.ESTABLISHED)
                status_updates_queue.put_nowait(statuses.SendingConnectionStateChanged.ESTABLISHED)
                await asyncio.sleep(1)


async def write_messages(reader, writer, sending_queue: asyncio.Queue, status_updates_queue, watchdog_queue):
    while message := await sending_queue.get():
        await write_message(message=f'{message}\n\n\n', writer=writer)
        watchdog_queue.put_nowait('Connection is alive. Message sent')


async def read_msgs(host, port, messages_queue, messages_to_save_queue, status_updates_queue, watchdog_queue):
    async with open_connection(host=host, port=port) as (reader, writer):
        while data := await reader.readline():
            message = data.decode()
            watchdog_queue.put_nowait('Connection is alive. New message in chat')
            messages_queue.put_nowait(message)
            messages_to_save_queue.put_nowait(message)


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


async def handle_connection(write_host, write_port, listen_host, listen_port, sending_queue, messages_queue, messages_to_save_queue, status_updates_queue, watchdog_queue):
    while True:
        try:
            async with reconnect(write_host, write_port) as (reader, writer):
                await authorise(reader=reader, writer=writer, status_updates_queue=status_updates_queue,
                                watchdog_queue=watchdog_queue)
                async with create_task_group() as task_group:
                    task_group.start_soon(write_messages, reader, writer, sending_queue, status_updates_queue, watchdog_queue)
                    task_group.start_soon(ping_pong, reader, writer, status_updates_queue, watchdog_queue)
                    task_group.start_soon(read_msgs, listen_host, listen_port, messages_queue, messages_to_save_queue, status_updates_queue, watchdog_queue)
                    task_group.start_soon(watch_for_connection, watchdog_queue)
        except (ConnectionError, ExceptionGroup) as exc:
            watchdog_queue.put_nowait('-------------------------ExceptionGroup--------------------------')
            status_updates_queue.put_nowait(statuses.ReadConnectionStateChanged.CLOSED)
            status_updates_queue.put_nowait(statuses.SendingConnectionStateChanged.CLOSED)
            await asyncio.sleep(1)
        else:
            status_updates_queue.put_nowait(statuses.ReadConnectionStateChanged.ESTABLISHED)
            status_updates_queue.put_nowait(statuses.SendingConnectionStateChanged.ESTABLISHED)


def main():
    messages_queue = asyncio.Queue()
    messages_to_save_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()
    try:
        anyio.run(draw, messages_queue, messages_to_save_queue, sending_queue, status_updates_queue, watchdog_queue)
    except (TkAppClosed, KeyboardInterrupt, ExceptionGroup):
        pass


if __name__ == '__main__':
    main()
