import asyncio
import curses
import random


async def blink(canvas, row, column, offset_tics, symbol):
    """Blink animation of specified star."""
    styles_time = ((curses.A_DIM, 20), (curses.A_NORMAL, 5), (curses.A_BOLD, 8), (curses.A_NORMAL, 5))

    for _ in range(offset_tics):
        await asyncio.sleep(0)

    while True:
        for style, max_seconds in styles_time:
            canvas.addstr(row, column, symbol, style)
            for _ in range(max_seconds):
                await asyncio.sleep(0)
