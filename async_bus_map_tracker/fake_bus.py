import argparse
import json
import logging
import os
from contextlib import suppress
from dataclasses import asdict
from itertools import chain, cycle, islice
from random import choice, randint

import trio
from dotenv import load_dotenv
from exceptiongroup import BaseExceptionGroup, ExceptionGroup
from trio_websocket import open_websocket_url

from async_bus_map_tracker.core.connections import relaunch_on_disconnect
from async_bus_map_tracker.core.types import Bus, ConfigData

load_dotenv()
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


def configure_application() -> ConfigData:
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', help='set server connection host')
    parser.add_argument('-rn', '--routes_number', help='set routes number')
    parser.add_argument('-bpr', '--buses_per_route', help='set amount of buses per route')
    parser.add_argument('-ws_n', '--websockets_number', help='set websockets number')
    parser.add_argument('-e_id', '--emulator_id', help='set emulator_id - prefix for busID')
    parser.add_argument('-rt', '--refresh_timeout', help='set refresh timeout for coordinates update')
    parser.add_argument('-v', '--logging', help='set logging settings')
    parser_args = parser.parse_args()
    return ConfigData(
        server=parser_args.server or os.getenv('SERVER_HOST', ''),
        routes_number=int(parser_args.routes_number or os.getenv('ROUTES_NUMBER', '')),
        buses_per_route=int(parser_args.buses_per_route or os.getenv('BUSSES_PER_ROUTE', '')),
        websockets_number=int(parser_args.websockets_number or os.getenv('WEBSOCKETS_NUMBER', '')),
        emulator_id=parser_args.emulator_id or os.getenv('PREFIX_EMULATOR_ID', ''),
        refresh_timeout=int(parser_args.refresh_timeout or os.getenv('COORD_REFRESH_TIMEOUT', '')),
        logging=parser_args.logging or os.getenv('LOGGING', ''),
    )


async def main():
    with suppress(KeyboardInterrupt, BaseExceptionGroup):
        config_data = configure_application()
        send_channel, receive_channel = trio.open_memory_channel(0)
        receiver_clones = [receive_channel.clone() for _ in range(config_data.websockets_number)]
        sender_clones = [send_channel.clone() for _ in range(config_data.websockets_number)]
        try:
            async with trio.open_nursery() as nursery:
                for i in range(config_data.websockets_number):
                    nursery.start_soon(send_updates, config_data.server, receiver_clones[i])

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
