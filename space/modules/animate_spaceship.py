import asyncio
from itertools import cycle

from modules.curses_tools import draw_frame, get_frame_size, read_controls


async def animate_spaceship(canvas, start_row, start_column, file_contents):
    max_rows, max_cols = canvas.getmaxyx()
    frame_to_size = {frame: get_frame_size(frame) for frame in file_contents}

    previous_row, previous_column = start_row, start_column
    previous_frame = file_contents[0]

    for step_text in cycle(file_contents):
        draw_frame(canvas, previous_row, previous_column, previous_frame, negative=True)
        draw_frame(canvas, start_row, start_column, step_text)
        canvas.refresh()

        previous_row, previous_column = start_row, start_column
        previous_frame = step_text

        for _ in range(2):
            rows_direction, columns_direction, space_pressed = read_controls(canvas=canvas)
            start_row = max(1, min(start_row + rows_direction, max_rows-frame_to_size[step_text][0]-1))
            start_column = max(1, min(start_column + columns_direction, max_cols-frame_to_size[step_text][1]-1))
            await asyncio.sleep(0)
        canvas.refresh()