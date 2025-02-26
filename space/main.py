import curses
from random import randint, choice

import consts
import globals
from modules.animate_spaceship import animate_spaceship
from modules.blink import blink
from modules.fire import fire
from modules.frames import load_frames_contents
from modules.space_garbage import fill_orbit_with_garbage
from modules.years import show_current_year_value, increment_year_value


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)
    # does not work on all terminals and OS
    # curses.curs_set(False)
    max_rows, max_cols = canvas.getmaxyx()
    frame_contents = load_frames_contents()
    year_info_window = canvas.derwin(1, consts.YEAR_INFO_WINDOW_WIDTH, max_rows-2, max_cols//2)

    globals.coroutines.append(fire(canvas=canvas, start_row=max_rows//2, start_column=max_cols//2))
    globals.coroutines.append(
        animate_spaceship(
            canvas=canvas,
            max_rows=max_rows,
            max_cols=max_cols,
            rocket_file_frames=frame_contents[consts.FileContentTypes.ROCKET],
            game_over_frame=frame_contents[consts.FileContentTypes.GAME_OVER][0],
        ),
    )
    globals.coroutines.append(
        fill_orbit_with_garbage(
            canvas=canvas,
            garbage_frames=frame_contents[consts.FileContentTypes.GARBAGE],
            explosion_frames=frame_contents[consts.FileContentTypes.EXPLOSION],
            max_cols=max_cols,
            max_rows=max_rows,
        ),
    )
    for col in range(1, max_cols-consts.CANVAS_BORDER_SIZE*2):
        globals.coroutines.append(blink(
            canvas=canvas,
            row=randint(1, max_rows-consts.CANVAS_BORDER_SIZE*2),
            column=col,
            offset_tics=randint(1, 20),
            symbol=choice(consts.STAR_SYMBOLS),
        ))
    globals.coroutines.append(show_current_year_value(year_info_window))
    globals.coroutines.append(increment_year_value())

    while True:
        for coroutine in globals.coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                globals.coroutines.remove(coroutine)
            except Exception as e:
                globals.coroutines.remove(coroutine)
                print(e)
        canvas.refresh()
        if len(globals.coroutines) == 0:
            break


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
