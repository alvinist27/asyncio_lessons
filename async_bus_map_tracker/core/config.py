import argparse
import os

from dotenv import load_dotenv

from async_bus_map_tracker.core.types import ConfigData

load_dotenv()


def configure_application() -> ConfigData:
    parser = argparse.ArgumentParser()
    parser.add_argument('-pr', '--server_protocol', help='set server connection protocol')
    parser.add_argument('-sh', '--server_host', help='set server connection host')
    parser.add_argument('-sp', '--server_port', help='set server connection port')
    parser.add_argument('-bp', '--browser_port', help='set browser connection port')
    parser.add_argument('-rn', '--routes_number', help='set routes number')
    parser.add_argument('-bpr', '--buses_per_route', help='set amount of buses per route')
    parser.add_argument('-ws_n', '--websockets_number', help='set websockets number')
    parser.add_argument('-e_id', '--emulator_id', help='set emulator_id - prefix for busID')
    parser.add_argument('-rt', '--refresh_timeout', help='set refresh timeout for coordinates update')
    parser.add_argument('-v', '--logging', help='set logging settings')
    parser_args = parser.parse_args()
    return ConfigData(
        server_protocol=parser_args.server_protocol or os.getenv('SERVER_PROTOCOL', ''),
        server_host=parser_args.server_host or os.getenv('SERVER_HOST', ''),
        server_port=int(parser_args.server_port or os.getenv('BUS_PORT', '')),
        browser_port=int(parser_args.browser_port or os.getenv('BROWSER_PORT', '')),
        routes_number=int(parser_args.routes_number or os.getenv('ROUTES_NUMBER', '')),
        buses_per_route=int(parser_args.buses_per_route or os.getenv('BUSES_PER_ROUTE', '')),
        websockets_number=int(parser_args.websockets_number or os.getenv('WEBSOCKETS_NUMBER', '')),
        emulator_id=parser_args.emulator_id or os.getenv('PREFIX_EMULATOR_ID', ''),
        refresh_timeout=int(parser_args.refresh_timeout or os.getenv('COORD_REFRESH_TIMEOUT', '')),
        logging=parser_args.logging or os.getenv('LOGGING', ''),
    )
