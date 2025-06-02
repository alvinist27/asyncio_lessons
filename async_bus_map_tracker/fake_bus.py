import json
import logging
from contextlib import suppress
from dataclasses import asdict
from itertools import chain, cycle, islice
from random import choice, randint

import trio
from trio_websocket import open_websocket_url

from async_bus_map_tracker.core import consts
from async_bus_map_tracker.core.config import configure_application
from async_bus_map_tracker.core.connections import relaunch_on_disconnect
from async_bus_map_tracker.core.routes import generate_bus_id, load_routes
from async_bus_map_tracker.core.models import Bus, MessageTypes

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


@relaunch_on_disconnect
async def send_updates(server_address: str, receive_channel: trio.MemoryReceiveChannel) -> None:
    async with open_websocket_url(server_address) as ws:
        logger.info(f'Open ws connection for {server_address}')
        async with receive_channel:
            async for value in receive_channel:
                await ws.send_message(value)
                logger.info(f'message send {value}')
                await trio.sleep(consts.SEND_UPDATES_TIMEOUT)


async def run_bus(
    send_channel: trio.MemorySendChannel,
    bus_index: int,
    bus_id: str,
    coordinates: tuple[float, float],
    refresh_timeout: int,
) -> None:
    async with send_channel:
        while True:
            for coordinate in islice(cycle(chain(coordinates, reversed(coordinates))), randint(10, 100)):
                lat, lng = coordinate
                message = {
                    'msgType': MessageTypes.BUSES.value,
                    'buses': asdict(Bus(
                        busId=generate_bus_id(bus_id, bus_index),
                        lat=lat,
                        lng=lng,
                        route=bus_id,
                    )),
                }
                await send_channel.send(json.dumps(message, ensure_ascii=True))
                await trio.sleep(refresh_timeout)
                logger.info(f'message send {message}')


async def main() -> None:
    with suppress(KeyboardInterrupt):
        config_data = configure_application()
        send_channel, receive_channel = trio.open_memory_channel(0)
        receiver_clones = [receive_channel.clone() for _ in range(config_data.websockets_number)]
        sender_clones = [send_channel.clone() for _ in range(config_data.websockets_number)]

        async with trio.open_nursery() as nursery:
            server_address = f'{config_data.server_protocol}{config_data.server_host}:{config_data.server_port}'
            for i in range(config_data.websockets_number):
                nursery.start_soon(send_updates, server_address, receiver_clones[i])

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


if __name__ == '__main__':
    trio.run(main)
