import logging
from dataclasses import asdict
from json import dumps, loads

import exceptiongroup
import trio
from trio_websocket import ConnectionClosed, serve_websocket

from async_bus_map_tracker.core.types import Bus, WindowBounds

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

buses = {}


async def send_buses(ws, bounds):
    busses = {}
    bounds_data = WindowBounds(**loads(bounds)['data'])
    for bus_id, bus in buses.items():
        if bounds_data.is_inside(bus.lat, bus.lng):
            busses[bus_id] = asdict(bus)
    logger.info(f'{len(busses)} buses inside bounds')
    message = dumps({"msgType": "Buses", "buses": list(busses.values())})
    await ws.send_message(message)


async def listen_browser(ws):
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
        await send_buses(ws, message)


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


async def talk_to_browser(request):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws)


async def main():
    try:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(serve_websocket, echo_server, '127.0.0.1', 8001, None)
            nursery.start_soon(serve_websocket, talk_to_browser, '127.0.0.1', 8080, None)
    except exceptiongroup.BaseExceptionGroup as exc:
        logger.error(exc)


if __name__ == '__main__':
    trio.run(main)
