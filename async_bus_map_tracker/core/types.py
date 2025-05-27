from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class ConfigData:
    server: str
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


@dataclass(frozen=True, kw_only=True, slots=True)
class WindowBounds:
    east_lng: float
    north_lat: float
    south_lat: float
    west_lng: float

    def is_inside(self, lat, lng):
        return (self.south_lat <= lat <= self.north_lat) and (self.west_lng <= lng <= self.east_lng)
