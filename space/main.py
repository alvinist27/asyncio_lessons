import curses
from random import randint

from modules.animate_spaceship import animate_spaceship
from modules.blink import blink
from modules.fire import fire


def init_file_contents():
    file_contents = []
    with open('modules/txt_frames/rocket_frame_1.txt', 'r', encoding='UTF-8') as first_file:
        file_contents.append(first_file.read())
    with open('modules/txt_frames/rocket_frame_2.txt', 'r', encoding='UTF-8') as second_file:
        file_contents.append(second_file.read())
    return file_contents


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)
    # curses.curs_set(False)
    max_rows, max_cols = canvas.getmaxyx()
    file_contents = init_file_contents()
    coroutines = [
        fire(canvas=canvas, start_row=max_rows // 2, start_column=max_cols // 2),
        animate_spaceship(canvas=canvas, start_row=(max_rows // 2) - 3, start_column=max_cols // 2, file_contents=file_contents),
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
