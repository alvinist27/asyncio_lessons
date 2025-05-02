from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class ConfigData:
    listen_host: str
    listen_port: str
    write_host: str
    write_port: str
    user_token: str
