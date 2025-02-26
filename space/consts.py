from enum import Enum
from types import MappingProxyType


STAR_SYMBOLS = '+*.:'
ROW_INDEX, COL_INDEX = 0, 1
PLASMA_GUN_START_YEAR = 2020
YEAR_TICKS = 150
YEAR_INFO_WINDOW_WIDTH = 50
CANVAS_BORDER_SIZE = 1
DEFAULT_GARBAGE_SPEED = 0.01
ISOLATED_TICKS_NUMBER = 2


PHRASES = MappingProxyType({
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
})


class FileContentTypes(Enum):
    EXPLOSION = 'explosion'
    GAME_OVER = 'game_over'
    GARBAGE = 'garbage'
    ROCKET = 'rocket'


BASE_FRAMES_PATH = 'modules/txt_frames'
ROCKET_FRAMES_DIR = f'{BASE_FRAMES_PATH}/rocket'
GARBAGE_FRAMES_DIR = f'{BASE_FRAMES_PATH}/garbage'
EXPLOSION_FRAMES_DIR = f'{BASE_FRAMES_PATH}/explosion'
GAME_OVER_FRAMES_DIR = f'{BASE_FRAMES_PATH}/game_over'


FILES_CONTENT_FRAMES = MappingProxyType({
    FileContentTypes.ROCKET: [
        f'{ROCKET_FRAMES_DIR}/rocket_frame_1.txt',
        f'{ROCKET_FRAMES_DIR}/rocket_frame_2.txt',
    ],
    FileContentTypes.GARBAGE: [
        f'{GARBAGE_FRAMES_DIR}/duck.txt',
        f'{GARBAGE_FRAMES_DIR}/hubble.txt',
        f'{GARBAGE_FRAMES_DIR}/lamp.txt',
        f'{GARBAGE_FRAMES_DIR}/trash_large.txt',
        f'{GARBAGE_FRAMES_DIR}/trash_small.txt',
        f'{GARBAGE_FRAMES_DIR}/trash_xl.txt',
    ],
    FileContentTypes.EXPLOSION: [
        f'{EXPLOSION_FRAMES_DIR}/explosion_1.txt',
        f'{EXPLOSION_FRAMES_DIR}/explosion_2.txt',
        f'{EXPLOSION_FRAMES_DIR}/explosion_3.txt',
        f'{EXPLOSION_FRAMES_DIR}/explosion_4.txt',
    ],
    FileContentTypes.GAME_OVER: [f'{GAME_OVER_FRAMES_DIR}/game_over.txt'],
})
