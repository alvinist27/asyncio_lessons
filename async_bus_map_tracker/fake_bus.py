import json
import logging
import os
from sys import stderr

import trio
from exceptiongroup import ExceptionGroup
from trio_websocket import open_websocket_url

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(url, bus_id, coordinates):
    try:
        async with open_websocket_url('ws://127.0.0.1:8001') as ws:
            for coordinate in coordinates:
                message = {
                    "msgType": "Buses",
                    "buses": [
                        {"busId": bus_id, "lat": coordinate[0], "lng": coordinate[1], "route": bus_id},
                    ]
                }
                await ws.send_message(json.dumps(message, ensure_ascii=True))
                await trio.sleep(1)
                logger.info(f'message send {message}')
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


async def main():
    try:
        async with trio.open_nursery() as nursery:
            for route in load_routes():
                nursery.start_soon(run_bus, '', route['name'], route['coordinates'])
    except ExceptionGroup as exc:
        print(exc)

if __name__ == '__main__':
    trio.run(main)
