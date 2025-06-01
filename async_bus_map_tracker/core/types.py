from dataclasses import dataclass
from enum import Enum


class MessageTypes(Enum):
    BUSES = 'Buses'
    NEW_BOUNDS = 'newBounds'

    def __str__(self) -> str:
        return str(self.value)

    @staticmethod
    def exists(value) -> bool:
        return value in set(item.value for item in MessageTypes)


class MessageErrors(Enum):
    INVALID_JSON = 'Requires valid JSON'
    NO_MSG_TYPE = 'Requires msgType specified'
    NO_DATA_IN_BOUNDS = 'Requires data specified'

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, kw_only=True, slots=True)
class ConfigData:
    server_protocol: str
    server_host: str
    server_port: int
    browser_port: int
    routes_number: int
    buses_per_route: int
    websockets_number: int
    emulator_id: str
    refresh_timeout: int
    logging: str


@dataclass(frozen=True, kw_only=True, slots=True)
class Bus:
    busId: str
    lat: float
    lng: float
    route: str


@dataclass(kw_only=True, slots=True)
class WindowBounds:
    east_lng: float = 0
    north_lat: float = 0
    south_lat: float = 0
    west_lng: float = 0

    def is_inside(self, lat, lng) -> bool:
        return (self.south_lat <= lat <= self.north_lat) and (self.west_lng <= lng <= self.east_lng)

    def update(self, east_lng, north_lat, south_lat, west_lng) -> None:
        self.east_lng, self.north_lat, self.south_lat, self.west_lng = east_lng, north_lat, south_lat, west_lng


@dataclass(frozen=True, kw_only=True, slots=True)
class MessageValidationError:
    error: MessageErrors
    message_type: str = 'Errors'

    def __str__(self):
        return '{"errors": [{}], "msgType": "{}"}'.format(self.error.value, self.message_type)
