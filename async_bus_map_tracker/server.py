import logging
from contextlib import suppress
from dataclasses import asdict
from json import dumps, loads

import trio
from trio_websocket import ConnectionClosed, serve_websocket

from async_bus_map_tracker.core.config import configure_application
from async_bus_map_tracker.core.types import Bus, WindowBounds

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

buses = {}


async def send_buses(ws, bounds: WindowBounds):
    """bounds mutable"""
    try:
        busses = {}

        for bus_id, bus in buses.items():
            if bounds.is_inside(bus.lat, bus.lng):
                busses[bus_id] = asdict(bus)
        logger.info(f'{len(busses)} buses inside bounds')
        message = dumps({"msgType": "Buses", "buses": list(busses.values())})
        await ws.send_message(message)
    except Exception as exc:
        print(exc)


async def listen_browser(ws, bounds: WindowBounds):
    """bounds mutable"""
    try:
        while True:
            message, counter = '', 0
            try:
                message = await ws.get_message()
            except ConnectionClosed:
                logger.error(ConnectionClosed)
            else:
                logger.info(f'received message {message}')

            if not message:
                continue
            bounds.update(**loads(message)['data'])
            await send_buses(ws, bounds)
    except Exception as exc:
        print(exc)


async def periodic_send_busses(ws, bounds: WindowBounds):
    try:
        while True:
            await send_buses(ws, bounds)
            await trio.sleep(1)
    except Exception as exc:
        print(exc)


async def talk_to_browser(request):
    bounds = WindowBounds()
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, bounds)
        nursery.start_soon(periodic_send_busses, ws, bounds)


async def echo_server(request):
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            await ws.send_message(message)
            json_message = loads(message)
            if json_message['msgType'] == 'Buses':
                buses[json_message['buses']['busId']] = Bus(**json_message['buses'])
            logger.info(f'message received: {message}')
        except ConnectionClosed:
            break
        except Exception as exc:
            print(exc)


async def main():
    config = configure_application()
    with suppress(KeyboardInterrupt):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(serve_websocket, echo_server, config.server_host, config.server_port, None)
            nursery.start_soon(serve_websocket, talk_to_browser, config.server_host, config.browser_port, None)


if __name__ == '__main__':
    trio.run(main)
