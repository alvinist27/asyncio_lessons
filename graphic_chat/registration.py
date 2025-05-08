import asyncio
import json
import logging
from tkinter import messagebox

import aiofiles
import anyio
from exceptiongroup import ExceptionGroup

from graphic_chat import choices, consts
from graphic_chat.chat import configure_application
from graphic_chat.connections import open_connection
from graphic_chat.exceptions import TkAppClosed
from graphic_chat.gui import draw
from graphic_chat.messages import read_message, write_message
from graphic_chat.chat_types import QueuesType


async def register(host: str, port: str, queues: QueuesType) -> None:
    async with open_connection(host, port) as (reader, writer):
        await read_message(reader=reader)
        await write_message(message=consts.SUBMIT_MESSAGE_CHARS, writer=writer)
        entry_message = await read_message(reader=reader)
        queues[choices.QueueNames.MESSAGES].put_nowait(f'{consts.REGISTRATION_START_MESSAGE} {entry_message}')

        username = await queues[choices.QueueNames.SENDING_MESSAGES].get()
        username_message = f'{username}{consts.SUBMIT_MESSAGE_CHARS}'
        await write_message(message=username_message, writer=writer)
        queues[choices.QueueNames.MESSAGES].put_nowait(username_message)

        auth_token_data = await read_message(reader=reader)
        try:
            json_message = json.loads(auth_token_data)
        except json.JSONDecodeError:
            logging.error(consts.REGISTRATION_ERROR_MESSAGE)
            raise
        async with aiofiles.open(consts.USER_HASH_FILE_NAME, mode='w') as hash_file:
            await hash_file.write(json_message['account_hash'])
        messagebox.showinfo(title=json_message["nickname"], message=consts.REGISTRATION_SUCCESS_MESSAGE)
        raise TkAppClosed


async def main() -> None:
    queues: dict[choices.QueueNames, asyncio.Queue] = {
        choices.QueueNames.MESSAGES: asyncio.Queue(),
        choices.QueueNames.SENDING_MESSAGES: asyncio.Queue(),
    }
    config_data = configure_application()
    async with anyio.create_task_group() as task_group:
        task_group.start_soon(draw, queues, False)
        task_group.start_soon(register, config_data.write_host, config_data.write_port, queues)


if __name__ == '__main__':
    try:
        anyio.run(main)
    except (TkAppClosed, KeyboardInterrupt, ExceptionGroup):
        pass
