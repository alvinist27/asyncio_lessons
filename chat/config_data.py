from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class ConfigData:
    host: str
    port: str
    history_file_path: str = ''
