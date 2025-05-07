import asyncio
import json
import logging
from asyncio import StreamReader, StreamWriter

import aiofiles
import anyio
from exceptiongroup import ExceptionGroup

from graphic_chat import choices, consts
from graphic_chat.chat import configure_application, ping_pong, watch_for_connection, write_chat_messages
from graphic_chat.connections import open_connection, reconnect
from graphic_chat.exceptions import TkAppClosed
from graphic_chat.gui import draw, set_connection_status
from graphic_chat.messages import read_message, write_message


async def register(host, port, queues) -> None:
    async with open_connection(host, port) as (reader, writer):
        queues[choices.QueueNames.WATCHDOG].put_nowait(consts.REGISTRATION_START_MESSAGE)
        message = await read_message(reader=reader)
        queues[choices.QueueNames.MESSAGES].put_nowait(message)
        await write_message(message='\n', writer=writer)
        await read_message(reader=reader)
        message = queues[choices.QueueNames.MESSAGES].put_nowait(message)
        queues[choices.QueueNames.MESSAGES].put_nowait(message)

        try:
            username = await queues[choices.QueueNames.SENDING_MESSAGES].get()
        except:
            print(exc)
        finally:
            print(username)

        await write_message(message=f'{username}{consts.SUBMIT_MESSAGE_CHARS}', writer=writer)
        auth_token_data = await read_message(reader=reader)
        try:
            json_message = json.loads(auth_token_data)
        except json.JSONDecodeError:
            logging.error(consts.REGISTRATION_ERROR_MESSAGE)
            raise
        async with aiofiles.open(consts.USER_HASH_FILE_NAME, mode='w') as hash_file:
            await hash_file.write(json_message['account_hash'])
        queues[choices.QueueNames.STATUS_UPDATES].put_nowait(choices.NicknameReceived(json_message['nickname']))

        # queues[choices.QueueNames.WATCHDOG].put_nowait(consts.REGISTRATION_START_MESSAGE)
        # queues[choices.QueueNames.MESSAGES].put_nowait(consts.REGISTRATION_SUCCESS_MESSAGE)


async def handle_connection(write_host, write_port, queues):
    while True:
        try:
            async with reconnect(write_host, write_port) as (reader, writer):
                async with anyio.create_task_group() as task_group:
                    # task_group.start_soon(write_chat_messages, writer, queues)
                    task_group.start_soon(ping_pong, reader, writer, queues)
                    task_group.start_soon(watch_for_connection, queues[choices.QueueNames.WATCHDOG])
                    task_group.start_soon(register, write_host, write_port, queues)
        except (ConnectionError, ExceptionGroup) as exc:
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


async def main():
    queues: dict[choices.QueueNames, asyncio.Queue] = {
        choices.QueueNames.MESSAGES: asyncio.Queue(),
        choices.QueueNames.SENDING_MESSAGES: asyncio.Queue(),
        choices.QueueNames.STATUS_UPDATES: asyncio.Queue(),
        choices.QueueNames.WATCHDOG: asyncio.Queue(),
    }

    config_data = configure_application()
    async with anyio.create_task_group() as task_group:
        task_group.start_soon(draw, queues)
        task_group.start_soon(
            handle_connection,
            config_data.write_host,
            config_data.write_port,
            queues,
        )


if __name__ == '__main__':
    try:
        anyio.run(main)
    except (TkAppClosed, KeyboardInterrupt, ExceptionGroup) as exc:
        pass
