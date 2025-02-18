import asyncio
from itertools import cycle

from modules.curses_tools import draw_frame, get_frame_size, read_controls
from modules.fire import fire
from modules.physycs import update_speed

ROW_INDEX = 0
COL_INDEX = 1


async def animate_spaceship(canvas, start_row, start_column, rocket_file_frames, game_over_frame):
    max_rows, max_cols = canvas.getmaxyx()
    frame_to_size = {frame: get_frame_size(frame) for frame in rocket_file_frames}

    previous_row, previous_column = start_row, start_column
    previous_frame = rocket_file_frames[0]

    row_speed = column_speed = 0
    for step_text in cycle(rocket_file_frames):
        draw_frame(canvas, previous_row, previous_column, previous_frame, negative=True)
        draw_frame(canvas, start_row, start_column, step_text)

        previous_row, previous_column = start_row, start_column
        previous_frame = step_text
        # await show_game_over(canvas, start_row, start_column, game_over_frame)
        for _ in range(2):
            rows_direction, columns_direction, space_pressed = read_controls(canvas=canvas)
            if space_pressed:
                await fire(canvas=canvas, start_row=start_row, start_column=start_column)



            row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
            start_row, start_column = start_row + row_speed, start_column + column_speed
            start_row = max(1, min(start_row, max_rows-frame_to_size[step_text][ROW_INDEX]-1))
            start_column = max(1, min(start_column, max_cols-frame_to_size[step_text][COL_INDEX]-1))
            await asyncio.sleep(0)
