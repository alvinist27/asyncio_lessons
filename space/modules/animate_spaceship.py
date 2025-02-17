import asyncio
from itertools import cycle

from modules.curses_tools import draw_frame, read_controls


async def animate_spaceship(canvas, start_row, start_column):
    file_contents = []
    with open('modules/txt_frames/rocket_frame_1.txt', 'r', encoding='UTF-8') as first_file:
        file_contents.append(first_file.read())
    with open('modules/txt_frames/rocket_frame_2.txt', 'r', encoding='UTF-8') as second_file:
        file_contents.append(second_file.read())
    for step_text in cycle(file_contents):
        print(step_text)
        draw_frame(canvas, start_row, start_column, step_text, negative=False)
        read_controls(canvas=canvas)
        for _ in range(2):
            await asyncio.sleep(0)
