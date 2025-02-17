import asyncio
import time
from itertools import cycle

from modules.curses_tools import draw_frame, read_controls


async def animate_spaceship(canvas, start_row, start_column, file_contents):
    for step_text in cycle(file_contents):
        draw_frame(canvas, start_row, start_column, step_text)
        for _ in range(2):
            rows_direction, columns_direction, space_pressed = read_controls(canvas=canvas)
            start_row += rows_direction
            start_column += columns_direction
            await asyncio.sleep(0)
        canvas.refresh()
