import asyncio

from modules.curses_tools import draw_frame, get_frame_size


async def show_game_over(canvas, center_row, center_column, game_over_frame):
    game_over_frame_rows, game_over_frame_columns = get_frame_size(game_over_frame)
    game_over_frame_start_row = center_row - game_over_frame_rows // 2
    game_over_frame__start_column = center_column - game_over_frame_columns // 2
    while True:
        draw_frame(canvas, game_over_frame_start_row, game_over_frame__start_column, game_over_frame)
        await asyncio.sleep(0)
