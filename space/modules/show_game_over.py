import asyncio

from consts import obstacles
from modules.curses_tools import draw_frame


async def show_game_over(canvas, row, column, frame):
    pass
    # for obstacle in obstacles:
    #     if obstacle.has_collision(row, column):
    #         await show_game_over(canvas=canvas, row=max_rows // 2, column=max_cols // 2, frame=game_over_frame)
    #         await asyncio.sleep(0)
    #
    # while True:
    #     draw_frame(canvas, row, column, frame)
    #     await asyncio.sleep(0)
