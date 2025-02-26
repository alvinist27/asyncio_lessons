import asyncio

from modules.curses_tools import draw_frame, get_frame_size


async def show_game_over(canvas, row, column, frame):
    frame_rows, frame_columns = get_frame_size(frame)
    while True:
        draw_frame(canvas, row-frame_rows//2, column-frame_columns//2, frame)
        await asyncio.sleep(0)
