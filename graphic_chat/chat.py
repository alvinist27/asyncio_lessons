import argparse
import asyncio
import logging
import os
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

import aiofiles
from dotenv import load_dotenv

from graphic_chat import choices, consts
from graphic_chat.config_data import ConfigData
from graphic_chat.connections import open_connection
from graphic_chat.exceptions import TkAppClosed

load_dotenv()
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def configure_application() -> ConfigData:
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--host', help='set connection host')
    parser.add_argument('-p', '--port', help='set connection port')
    parser.add_argument('-t', '--token', help='set user auth token')
    parser_args = parser.parse_args()
    return ConfigData(
        server_host=parser_args.host or os.getenv('SERVER_HOST', ''),
        server_port=parser_args.port or os.getenv('SERVER_PORT', ''),
        user_token=parser_args.token or os.getenv('USER_TOKEN', ''),
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
        if isinstance(msg, choices.ReadConnectionStateChanged):
            read_label['text'] = f'Чтение: {msg}'

        if isinstance(msg, choices.SendingConnectionStateChanged):
            write_label['text'] = f'Отправка: {msg}'

        if isinstance(msg, choices.NicknameReceived):
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


async def draw(messages_queue, messages_to_save_queue, sending_queue, status_updates_queue):
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
        update_tk(root_frame),
        update_status_panel(status_labels, status_updates_queue),
        update_conversation_history(conversation_panel, messages_queue),
        read_msgs(config_data.server_host, config_data.server_port, messages_queue, messages_to_save_queue),
        save_msgs(messages_to_save_queue)
    )


async def read_msgs(host, port, messages_queue, messages_to_save_queue):
    async with open_connection(host=host, port=port) as (reader, writer):
        while data := await reader.readline():
            message = data.decode()
            messages_queue.put_nowait(message)
            messages_to_save_queue.put_nowait(message)


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

    loop.run_until_complete(draw(messages_queue, messages_to_save_queue, sending_queue, status_updates_queue))


if __name__ == '__main__':
    main()
