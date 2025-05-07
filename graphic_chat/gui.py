import asyncio
import logging
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from anyio import create_task_group

from graphic_chat import choices, consts
from graphic_chat.choices import QueueNames
from graphic_chat.exceptions import TkAppClosed

logger = logging.getLogger('base')


async def update_tk(root_frame, interval=consts.TK_FRAME_UPDATE_INTERVAL):
    while True:
        try:
            root_frame.update()
        except tk.TclError:
            raise TkAppClosed()
        await asyncio.sleep(interval)


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


def set_connection_status(update_state_queue, read_state, write_state) -> None:
    update_state_queue.put_nowait(read_state)
    update_state_queue.put_nowait(write_state)


def process_new_message(input_field, sending_queue):
    text = input_field.get()
    sending_queue.put_nowait(text)
    logger.info(f'Пользователь написал: {text}')
    input_field.delete(0, tk.END)


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


async def draw(queues):
    root = tk.Tk()

    root.title('Чат Майнкрафтера')

    root_frame = tk.Frame()
    root_frame.pack(fill='both', expand=True)

    status_labels = create_status_panel(root_frame)

    input_frame = tk.Frame(root_frame)
    input_frame.pack(side='bottom', fill=tk.X)

    input_field = tk.Entry(input_frame)
    input_field.pack(side='left', fill=tk.X, expand=True)

    input_field.bind('<Return>', lambda event: process_new_message(input_field, queues[QueueNames.SENDING_MESSAGES]))

    send_button = tk.Button(input_frame)
    send_button['text'] = 'Отправить'
    send_button['command'] = lambda: process_new_message(input_field, queues[QueueNames.SENDING_MESSAGES])
    send_button.pack(side='left')

    conversation_panel = ScrolledText(root_frame, wrap='none')
    conversation_panel.pack(side='top', fill='both', expand=True)

    async with create_task_group() as task_group:
        task_group.start_soon(update_tk, root_frame)
        task_group.start_soon(update_status_panel, status_labels, queues[QueueNames.STATUS_UPDATES])
        task_group.start_soon(update_conversation_history, conversation_panel, queues[QueueNames.MESSAGES])
