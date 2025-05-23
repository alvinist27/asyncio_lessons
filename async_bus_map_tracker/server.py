import logging
from json import dumps, loads

import trio
from exceptiongroup import ExceptionGroup
from trio_websocket import ConnectionClosed, serve_websocket

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

buses = {}


async def echo_server(request):
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            await ws.send_message(message)
            json_message = loads(message)
            if json_message['msgType'] == 'Buses':
                buses[json_message['buses'][0]['busId']] = json_message['buses'][0]
            logger.info(f'message received: {message}')
        except ConnectionClosed:
            break
        except Exception as exc:
            print(exc)


async def talk_to_browser(request):
    ws = await request.accept()
    while True:
        try:
            message = dumps({"msgType": "Buses", "buses": list(buses.values())})
            await ws.send_message(message)
            logger.info(f'message sent: {message}')
        except ConnectionClosed:
            break
        except Exception as exc:
            print(exc)


async def main():
    try:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(serve_websocket, echo_server, '127.0.0.1', 8001, None)
            nursery.start_soon(serve_websocket, talk_to_browser, '127.0.0.1', 8080, None)
    except ExceptionGroup as exc:
        logger.error(exc)


if __name__ == '__main__':
    trio.run(main)
