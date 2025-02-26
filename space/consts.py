from enum import Enum
from types import MappingProxyType


class FileContentTypes(Enum):
    ROCKET = 'rocket'
    GARBAGE = 'garbage'
    GAME_OVER = 'game_over'


FILES_CONTENT_FRAMES = MappingProxyType({
    FileContentTypes.ROCKET: [
        'modules/txt_frames/rocket_frame_1.txt',
        'modules/txt_frames/rocket_frame_2.txt',
    ],
    FileContentTypes.GARBAGE: [
        'modules/txt_frames/duck.txt',
        'modules/txt_frames/hubble.txt',
        'modules/txt_frames/lamp.txt',
        'modules/txt_frames/trash_large.txt',
        'modules/txt_frames/trash_small.txt',
        'modules/txt_frames/trash_xl.txt',
    ],
    FileContentTypes.GAME_OVER: ['modules/txt_frames/game_over.txt'],
})
