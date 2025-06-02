from json import loads

import pytest
from trio_websocket import open_websocket_url

from async_bus_map_tracker.core.config import configure_application
from async_bus_map_tracker.core.models import MessageErrors

config_data = configure_application(is_test=True)
SERVER_HOST = f'{config_data.server_protocol}{config_data.server_host}'
ERROR_MESSAGE_RETRY_AMOUNT = 5


@pytest.fixture
async def server_client():
    async with open_websocket_url(f'{SERVER_HOST}:{config_data.server_port}') as ws:
        yield ws


@pytest.fixture
async def browser_bus_client():
    async with open_websocket_url(f'{SERVER_HOST}:{config_data.browser_port}') as ws:
        yield ws


@pytest.mark.trio
@pytest.mark.parametrize('payload, error', [
    ('{123:112,', MessageErrors.INVALID_JSON.value),
    (
        '{"data": {"east_lng": 37.0, "north_lat": 55.0, "south_lat": 55.0, "west_lng": 37.5}}',
        MessageErrors.NO_MSG_TYPE.value,
    ),
    (
        '{"msgType": "newBounds", "1": {"east_lng": 37.0, "north_lat": 55.0, "south_lat": 55.0, "west_lng": 37.5}}',
        MessageErrors.NO_DATA_IN_BOUNDS.value,
    ),
])
async def test_server_client(server_client, payload, error):
    await server_client.send_message(payload)
    response = await server_client.get_message()
    assert response == f'{{"errors": ["{error}"], "msgType": "Errors"}}'


async def get_error_message(ws):
    for _ in range(ERROR_MESSAGE_RETRY_AMOUNT):
        response = await ws.get_message()
        data = loads(response)
        if data.get("msgType") == "Errors":
            return response
    raise AssertionError("No Errors message received")


@pytest.mark.trio
@pytest.mark.parametrize('payload, error', [
    ('{"msgType": "Buses", "buses": [}', MessageErrors.INVALID_JSON.value),
    (
        '{"buses": [{"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"}]}',
        MessageErrors.NO_MSG_TYPE.value,
    ),
])
async def test_browser_client(browser_bus_client, payload, error):
    await browser_bus_client.send_message(payload)
    response = await get_error_message(browser_bus_client)
    assert response == f'{{"errors": ["{error}"], "msgType": "Errors"}}'
