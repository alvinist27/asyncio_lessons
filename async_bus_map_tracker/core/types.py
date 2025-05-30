from dataclasses import dataclass


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

    def is_inside(self, lat, lng):
        return (self.south_lat <= lat <= self.north_lat) and (self.west_lng <= lng <= self.east_lng)

    def update(self, south_lat, north_lat, west_lng, east_lng):
        self.south_lat, self.north_lat, self.west_lng, self.east_lng = south_lat, north_lat, west_lng, east_lng
