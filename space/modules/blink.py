import curses

from modules.sleep import async_sleep


async def blink(canvas, row, column, offset_tics, symbol):
    """Blink animation of specified star."""
    styles_time = ((curses.A_DIM, 20), (curses.A_NORMAL, 5), (curses.A_BOLD, 8), (curses.A_NORMAL, 5))

    await async_sleep(offset_tics)

    while True:
        for style, delay_seconds in styles_time:
            canvas.addstr(row, column, symbol, style)
            await async_sleep(delay_seconds)

