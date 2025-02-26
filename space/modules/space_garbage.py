import asyncio
from random import choice, randint

import consts
import globals
from modules.curses_tools import draw_frame, get_frame_size
from modules.explosion import explode
from modules.game_scenario import get_garbage_delay_tics
from modules.obstacles import Obstacle
from modules.sleep import async_sleep


async def fill_orbit_with_garbage(canvas, garbage_frames, explosion_frames, max_rows, max_cols):
    while True:
        delay = get_garbage_delay_tics(globals.year)
        if delay:
            globals.coroutines.append(
                fly_garbage(
                    canvas=canvas,
                    column=randint(consts.CANVAS_BORDER_SIZE, max_cols-consts.CANVAS_BORDER_SIZE),
                    garbage_frame=choice(garbage_frames),
                    explosion_frames=explosion_frames,
                    speed=consts.DEFAULT_GARBAGE_SPEED,
                    max_rows=max_rows,
                    max_cols=max_cols,
                ),
            )
        await async_sleep(delay or 1)


async def fly_garbage(
    canvas,
    max_rows,
    max_cols,
    column,
    garbage_frame,
    explosion_frames,
    speed=consts.DEFAULT_GARBAGE_SPEED,
):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    frame_rows, frame_columns = get_frame_size(garbage_frame)
    column = min(max(column, 0), max_cols - consts.CANVAS_BORDER_SIZE)

    obstacle = Obstacle(row=0, column=column, rows_size=frame_rows, columns_size=frame_columns)
    globals.obstacles.append(obstacle)

    while obstacle.row < max_rows:
        if obstacle in globals.obstacles_in_last_collisions:
            globals.obstacles_in_last_collisions.remove(obstacle)
            await explode(canvas, obstacle.row + frame_rows // 2, column + frame_columns // 2, explosion_frames)
            break
        draw_frame(canvas, obstacle.row, obstacle.column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, obstacle.row, obstacle.column, garbage_frame, negative=True)
        obstacle.row += speed
    globals.obstacles.remove(obstacle)
