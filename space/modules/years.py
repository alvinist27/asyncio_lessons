import asyncio

import consts
import globals
from modules.curses_tools import draw_frame
from modules.sleep import async_sleep


async def increment_year_value():
    while True:
        await async_sleep(consts.YEAR_TICKS)
        globals.year += 1


async def show_current_year_value(canvas):
    while True:
        message = f'Year: {globals.year} {consts.PHRASES.get(globals.year, "")}'
        draw_frame(canvas, 0, 0, message)
        await asyncio.sleep(0)
        draw_frame(canvas, 0, 0, message, negative=True)
