import curses
from random import randint

from modules.animate_spaceship import animate_spaceship
from modules.blink import blink
from modules.fire import fire


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)
    # curses.curs_set(False)
    max_rows, max_cols = canvas.getmaxyx()
    coroutines = [
        fire(canvas=canvas, start_row=max_rows // 2, start_column=max_cols // 2),
        animate_spaceship(canvas=canvas, start_row=(max_rows // 2) - 3, start_column=max_cols // 2),
    ]
    for col in range(1, max_cols-2):
        coroutines.append(blink(canvas=canvas, row=randint(1, max_rows-2), column=col))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
            except Exception as e:
                coroutines.remove(coroutine)
                print(e)
            canvas.refresh()
        if len(coroutines) == 0:
            break


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
