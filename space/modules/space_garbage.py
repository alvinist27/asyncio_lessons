import asyncio
from random import choice, randint

from consts import coroutines, obstacles, obstacles_in_last_collisions
from modules.curses_tools import draw_frame, get_frame_size
from modules.obstacles import Obstacle
from modules.sleep import async_sleep


async def fill_orbit_with_garbage(canvas, garbage_frames):
    _, columns_number = canvas.getmaxyx()
    while True:
        coroutines.append(fly_garbage(
            canvas=canvas,
            column=randint(1, columns_number),
            garbage_frame=choice(garbage_frames),
            speed=0.01
        ))
        await async_sleep(1000)


async def fly_garbage(canvas, column, garbage_frame, speed=0.01):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(garbage_frame)

    column = max(column, 0)
    column = min(column, columns_number - 1)

    obstacle = Obstacle(row=0, column=column, rows_size=frame_rows, columns_size=frame_columns)
    obstacles.append(obstacle)

    while obstacle.row < rows_number:
        if obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.remove(obstacle)
            break
        draw_frame(canvas, obstacle.row, obstacle.column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, obstacle.row, obstacle.column, garbage_frame, negative=True)
        obstacle.row += speed
    obstacles.remove(obstacle)
