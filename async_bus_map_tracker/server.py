import logging
from contextlib import suppress
from dataclasses import asdict
from json import dumps

import trio
from trio_websocket import ConnectionClosed, serve_websocket, WebSocketConnection, WebSocketRequest

from async_bus_map_tracker.core import consts
from async_bus_map_tracker.core.config import configure_application
from async_bus_map_tracker.core.models import Bus, MessageTypes, MessageValidationError, WindowBounds
from async_bus_map_tracker.core.validators import JsonMessageValidator

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

buses = {}


async def send_buses(ws: WebSocketConnection, bounds: WindowBounds) -> None:
    """Send buses to websocket.

    Args:
        ws: WebSocketConnection instance;
        bounds: mutable argument as WindowBounds instance.
    """
    try:
        bounds_buses = {}
        for bus_id, bus in bounds_buses.items():
            if bounds.is_inside(bus.lat, bus.lng):
                bounds_buses[bus_id] = asdict(bus)
        logger.info(f'{len(bounds_buses)} buses inside bounds')
        message = dumps({'msgType': MessageTypes.BUSES.value, 'buses': list(bounds_buses.values())})
        await ws.send_message(message)
    except Exception as exc:
        print(exc)


async def listen_browser(ws: WebSocketConnection, bounds: WindowBounds) -> None:
    """Listen browser websocket .

    Args:
        ws: WebSocketConnection instance;
        bounds: mutable argument as WindowBounds instance.
    """
    while True:
        try:
            message = await ws.get_message()
        except ConnectionClosed as exc:
            logger.error(f'ConnectionClosed {exc}')
            raise exc
        else:
            logger.info(f'received message {message}')

        if not message:
            continue
        json_message = JsonMessageValidator(message=message, is_bounds=True).get_validated_data()
        if isinstance(json_message, MessageValidationError):
            await ws.send_message(str(json_message))
            continue
        bounds.update(**json_message)
        await send_buses(ws, bounds)


async def periodic_send_buses(ws: WebSocketConnection, bounds: WindowBounds) -> None:
    """Send buses specified amount of seconds.

    Args:
        ws: WebSocketConnection instance;
        bounds: mutable argument as WindowBounds instance.
    """
    while True:
        await send_buses(ws, bounds)
        await trio.sleep(consts.BUSES_UPDATE_TIMEOUT)


async def talk_to_browser(request: WebSocketRequest) -> None:
    ws = await request.accept()
    bounds = WindowBounds()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, bounds)
        nursery.start_soon(periodic_send_buses, ws, bounds)


async def handle_bus_messages(request: WebSocketRequest) -> None:
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            json_message = JsonMessageValidator(message=message, is_bounds=True).get_validated_data()
            if isinstance(json_message, MessageValidationError):
                await ws.send_message(str(json_message))
                continue

            if json_message['msgType'] == MessageTypes.BUSES:
                buses[json_message['buses']['busId']] = Bus(**json_message['buses'])
            logger.info(f'message received: {message}')
        except ConnectionClosed:
            break


async def main() -> None:
    config = configure_application()
    with suppress(KeyboardInterrupt):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(serve_websocket, handle_bus_messages, config.server_host, config.server_port, None)
            nursery.start_soon(serve_websocket, talk_to_browser, config.server_host, config.browser_port, None)


if __name__ == '__main__':
    trio.run(main)
