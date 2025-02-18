import curses
from collections import defaultdict
from random import randint, choice

from consts import FileContentTypes, FILES_CONTENT_FRAMES, coroutines
from modules.animate_spaceship import animate_spaceship
from modules.blink import blink
from modules.fire import fire
from modules.space_garbage import fill_orbit_with_garbage


def init_file_contents():
    file_contents = defaultdict(list)
    for file_content_type, file_content_paths in FILES_CONTENT_FRAMES.items():
        for file_content_path in file_content_paths:
            with open(file_content_path, 'r', encoding='UTF-8') as frame_file:
                file_contents[file_content_type].append(frame_file.read())
    return file_contents


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)
    # работает не на всех терминалах
    # curses.curs_set(False)
    max_rows, max_cols = canvas.getmaxyx()
    file_contents = init_file_contents()

    coroutines.append(fire(canvas=canvas, start_row=max_rows // 2, start_column=max_cols // 2))
    coroutines.append(
        animate_spaceship(
            canvas=canvas,
            start_row=(max_rows // 2) - 3,
            start_column=max_cols // 2,
            rocket_file_frames=file_contents[FileContentTypes.ROCKET],
            game_over_frame=file_contents[FileContentTypes.ROCKET][0],
        ),
    )
    coroutines.append(fill_orbit_with_garbage(canvas=canvas, garbage_frames=file_contents[FileContentTypes.GARBAGE]))
    for col in range(1, max_cols-2):
        coroutines.append(blink(
            canvas=canvas,
            row=randint(1, max_rows-2),
            column=col,
            offset_tics=randint(1, 20),
            symbol=choice('+*.:'),
        ))

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
