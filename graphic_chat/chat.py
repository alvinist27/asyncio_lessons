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
from dotenv import load_dotenv

from graphic_chat import consts, statuses
from graphic_chat.config_data import ConfigData
from graphic_chat.connections import open_connection
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
    await asyncio.gather(
        write_messages(config_data.write_host, config_data.write_port, sending_queue, status_updates_queue, watchdog_queue),
        update_tk(root_frame),
        update_status_panel(status_labels, status_updates_queue),
        update_conversation_history(conversation_panel, messages_queue),
        read_msgs(config_data.listen_host, config_data.listen_port, messages_queue, messages_to_save_queue, status_updates_queue, watchdog_queue),
        save_msgs(messages_to_save_queue),
        watch_for_connection(watchdog_queue),
    )


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
    message = 'watchdog logging started'
    while message:
        watchdog_logger.info(f'[{int(time.time())}] {message}')

        # async with timeout(1) as timeout_data:
        #     message = await queue.get()
        #     if timeout_data.expired:
        #         watchdog_logger.info(f'[{int(time.time())}] 1s timeout is elapsed')
        #     else:
        #
        #     timeout_data.reschedule(None)


async def authorise(reader: StreamReader, writer: StreamWriter, status_updates_queue: asyncio.Queue, watchdog_queue) -> None:
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
            messagebox.showerror(title='Неверный токен', message=consts.TOKEN_ERROR_MESSAGE)
            logger.error(consts.TOKEN_ERROR_MESSAGE)
        else:
            status_updates_queue.put_nowait(statuses.NicknameReceived(json_message['nickname']))
            watchdog_queue.put_nowait('Connection is alive.Authorization done')
            logger.info(f'Выполнена авторизация. Пользователь {json_message["nickname"]}')


async def write_messages(host, port, sending_queue, status_updates_queue, watchdog_queue):
    status_updates_queue.put_nowait(statuses.SendingConnectionStateChanged.INITIATED)
    async with open_connection(host=host, port=port) as (reader, writer):
        status_updates_queue.put_nowait(statuses.SendingConnectionStateChanged.ESTABLISHED)
        watchdog_queue.put_nowait('Prompt before auth')

        await authorise(reader=reader, writer=writer, status_updates_queue=status_updates_queue, watchdog_queue=watchdog_queue)
        while message := await sending_queue.get():
            await write_message(message=f'{message}\n\n\n', writer=writer)
            watchdog_queue.put_nowait('Connection is alive. Message sent')
    status_updates_queue.put_nowait(statuses.SendingConnectionStateChanged.CLOSED)


async def read_msgs(host, port, messages_queue, messages_to_save_queue, status_updates_queue, watchdog_queue):
    status_updates_queue.put_nowait(statuses.ReadConnectionStateChanged.INITIATED)
    async with open_connection(host=host, port=port) as (reader, writer):
        status_updates_queue.put_nowait(statuses.ReadConnectionStateChanged.ESTABLISHED)
        while data := await reader.readline():
            message = data.decode()
            watchdog_queue.put_nowait('Connection is alive. New message in chat')
            messages_queue.put_nowait(message)
            messages_to_save_queue.put_nowait(message)
    status_updates_queue.put_nowait(statuses.ReadConnectionStateChanged.CLOSED)


async def preload_chat_history(messages_queue: asyncio.Queue):
    async with aiofiles.open(consts.CHAT_HISTORY_FILE_NAME, 'r') as history_file:
        while data := await history_file.readline():
            messages_queue.put_nowait(data)


async def save_msgs(messages_to_save_queue):
    async with aiofiles.open(consts.CHAT_HISTORY_FILE_NAME, 'a') as history_file:
        while True:
            message = await messages_to_save_queue.get()
            await history_file.write(message)


def main():
    loop = asyncio.get_event_loop()
    messages_queue = asyncio.Queue()
    messages_to_save_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()
    loop.run_until_complete(draw(messages_queue, messages_to_save_queue, sending_queue, status_updates_queue, watchdog_queue))


if __name__ == '__main__':
    main()
