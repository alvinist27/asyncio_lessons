import asyncio
import curses
import random


async def blink(canvas, row, column):
    """Blink animation of specified star."""
    symbol = random.choice('+*.:')
    styles_time = ((curses.A_DIM, 2000), (curses.A_NORMAL, 500), (curses.A_BOLD, 800), (curses.A_NORMAL, 500))
    while True:
        for style, max_seconds in styles_time:
            canvas.addstr(row, column, symbol, style)
            for _ in range(random.randint(10, max_seconds)):
                await asyncio.sleep(0)
