from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class ConfigData:
    server_host: str
    server_port: str
    user_token: str
