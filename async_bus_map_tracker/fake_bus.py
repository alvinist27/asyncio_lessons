import json
import logging
import os
from contextlib import suppress
from dataclasses import asdict
from itertools import chain, cycle, islice
from random import choice, randint

import trio
from exceptiongroup import BaseExceptionGroup, ExceptionGroup
from trio_websocket import open_websocket_url

from async_bus_map_tracker.core.config import configure_application
from async_bus_map_tracker.core.connections import relaunch_on_disconnect
from async_bus_map_tracker.core.types import Bus

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def generate_bus_id(route_id, bus_index):
    return f"{route_id}-{bus_index}"


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


@relaunch_on_disconnect
async def send_updates(server_address, receive_channel):
    async with open_websocket_url(server_address) as ws:
        async with receive_channel:
            async for value in receive_channel:
                await ws.send_message(value)
                logger.info(f'message send {value}')


async def run_bus(send_channel, bus_index, bus_id, coordinates, refresh_timeout):
    async with send_channel:
        while True:
            for coordinate in islice(cycle(chain(coordinates, reversed(coordinates))), randint(10, 100)):
                message = {
                    "msgType": "Buses",
                    "buses": asdict(Bus(
                        busId=generate_bus_id(bus_id, bus_index),
                        lat=coordinate[0],
                        lng=coordinate[1],
                        route=bus_id
                    )),
                }
                await send_channel.send(json.dumps(message, ensure_ascii=True))
                await trio.sleep(refresh_timeout)
                print(message)
                logger.info(f'message send {message}')


async def main():
    with suppress(KeyboardInterrupt, BaseExceptionGroup):
        config_data = configure_application()
        send_channel, receive_channel = trio.open_memory_channel(0)
        receiver_clones = [receive_channel.clone() for _ in range(config_data.websockets_number)]
        sender_clones = [send_channel.clone() for _ in range(config_data.websockets_number)]
        try:
            async with trio.open_nursery() as nursery:
                for i in range(config_data.websockets_number):
                    nursery.start_soon(
                        send_updates,
                        f'{config_data.server_protocol}{config_data.server_host}:{config_data.server_port}',
                        receiver_clones[i],
                    )

                routes = list(load_routes())[:config_data.routes_number]
                for route in routes:
                    for bus_index in range(config_data.buses_per_route):
                        channel = choice(sender_clones)
                        nursery.start_soon(
                            run_bus,
                            channel,
                            bus_index,
                            f"{config_data.emulator_id}{route['name']}",
                            route['coordinates'],
                            config_data.refresh_timeout,
                        )
        except ExceptionGroup as exc:
            print(exc)

if __name__ == '__main__':
    trio.run(main)
