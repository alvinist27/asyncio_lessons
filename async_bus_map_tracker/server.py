import logging
from contextlib import suppress
from dataclasses import asdict
from functools import partial
from json import dumps
from typing import Any

import trio
from trio_websocket import ConnectionClosed, serve_websocket, WebSocketConnection, WebSocketRequest

from async_bus_map_tracker.core import consts
from async_bus_map_tracker.core.config import configure_application
from async_bus_map_tracker.core.models import Bus, MessageTypes, MessageValidationError, WindowBounds
from async_bus_map_tracker.core.validators import JsonMessageValidator

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


async def send_buses(ws: WebSocketConnection, bounds: WindowBounds, registered_buses: dict[str, Any]) -> None:
    """Send buses to websocket.

    Args:
        ws: WebSocketConnection instance;
        registered_buses: all busses data from clients;
        bounds: mutable argument as WindowBounds instance.
    """
    bounds_buses = {}
    for bus_id, bus in registered_buses.items():
        if bounds.is_inside(bus.lat, bus.lng):
            bounds_buses[bus_id] = asdict(bus)
    logger.info(f'{len(bounds_buses)} buses inside bounds')
    message = dumps({'msgType': MessageTypes.BUSES.value, 'buses': list(bounds_buses.values())})
    await ws.send_message(message)


async def listen_browser(ws: WebSocketConnection, bounds: WindowBounds, registered_buses: dict[str, Any]) -> None:
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
            break
        else:
            logger.info(f'received message {message}')

        if not message:
            continue
        json_message = JsonMessageValidator(message=message).get_validated_data()
        if isinstance(json_message, MessageValidationError):
            await ws.send_message(str(json_message))
            continue
        bounds.update(**json_message)
        await send_buses(ws, bounds, registered_buses)


async def periodic_send_buses(
    ws: WebSocketConnection,
    bounds: WindowBounds,
    update_timeout: float,
    registered_buses: dict[str, Any],
) -> None:
    """Send buses specified amount of seconds.

    Args:
        ws: WebSocketConnection instance;
        update_timeout: periodic timeout in seconds;
        registered_buses: all busses data from clients;
        bounds: mutable argument as WindowBounds instance.
    """
    while True:
        await send_buses(ws, bounds, registered_buses)
        await trio.sleep(update_timeout)


async def talk_to_browser(request: WebSocketRequest, update_timeout: float, registered_buses: dict[str, Any]) -> None:
    ws = await request.accept()
    bounds = WindowBounds()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, bounds, registered_buses)
        nursery.start_soon(periodic_send_buses, ws, bounds, update_timeout, registered_buses)


async def get_bus_messages(request: WebSocketRequest, registered_buses: dict[str, Any]) -> None:
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            json_message = JsonMessageValidator(message=message).get_validated_data()
            if isinstance(json_message, MessageValidationError):
                await ws.send_message(str(json_message))
                continue

            if json_message['msgType'] == MessageTypes.BUSES.value:
                registered_buses[json_message['buses']['busId']] = Bus(**json_message['buses'])
            logger.info(f'message received: {message}')
        except ConnectionClosed:
            break


async def main() -> None:
    config = configure_application()
    registered_buses = {}
    handle_bus_messages = partial(get_bus_messages, registered_buses=registered_buses)
    handle_talk_to_browser = partial(
        talk_to_browser,
        update_timeout=consts.BUSES_UPDATE_TIMEOUT,
        registered_buses=registered_buses,
    )

    with suppress(KeyboardInterrupt):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(serve_websocket, handle_bus_messages, config.server_host, config.server_port, None)
            nursery.start_soon(serve_websocket, handle_talk_to_browser, config.server_host, config.browser_port, None)


if __name__ == '__main__':
    trio.run(main)
