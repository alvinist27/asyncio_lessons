from collections import defaultdict

from consts import FILES_CONTENT_FRAMES


def load_frames_contents():
    file_contents = defaultdict(list)
    for file_content_type, file_content_paths in FILES_CONTENT_FRAMES.items():
        for file_content_path in file_content_paths:
            with open(file_content_path, 'r', encoding='UTF-8') as frame_file:
                file_contents[file_content_type].append(frame_file.read())
    return file_contents
