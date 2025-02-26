import asyncio
from itertools import cycle

import consts
import globals
from modules.curses_tools import draw_frame, get_frame_size, read_controls
from modules.fire import fire
from modules.physycs import update_speed
from modules.show_game_over import show_game_over


async def animate_spaceship(canvas, max_rows, max_cols, rocket_file_frames, game_over_frame):
    current_row, current_column = max_rows // 2, max_cols // 2
    frame_to_size = {frame: get_frame_size(frame) for frame in rocket_file_frames}

    rocket_rows, rocket_columns = frame_to_size[rocket_file_frames[0]]

    previous_row, previous_column = current_row, current_column
    previous_frame = rocket_file_frames[0]

    row_speed = column_speed = 0
    for rocket_frame in cycle(rocket_file_frames):
        draw_frame(canvas, previous_row, previous_column, previous_frame, negative=True)
        draw_frame(canvas, current_row, current_column, rocket_frame)
        previous_row, previous_column, previous_frame = current_row, current_column, rocket_frame

        for _ in range(consts.ISOLATED_TICKS_NUMBER):
            rows_direction, columns_direction, space_pressed = read_controls(canvas=canvas)
            if space_pressed and globals.year >= consts.PLASMA_GUN_START_YEAR:
                await fire(canvas=canvas, start_row=current_row, start_column=current_column)
            for obstacle in globals.obstacles:
                if obstacle.has_collision(current_row, current_column, rocket_rows, rocket_columns):
                    draw_frame(canvas, current_row, current_column, rocket_frame, negative=True)
                    await show_game_over(
                        canvas=canvas,
                        center_row=max_rows//2,
                        center_column=max_cols//2,
                        game_over_frame=game_over_frame,
                    )
            row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
            current_row, current_column = current_row + row_speed, current_column + column_speed
            current_row = max(1, min(current_row, max_rows-frame_to_size[rocket_frame][consts.ROW_INDEX]-1))
            current_column = max(1, min(current_column, max_cols-frame_to_size[rocket_frame][consts.COL_INDEX]-1))
            await asyncio.sleep(0)
