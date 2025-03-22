import asyncio
import os.path

import aiofiles
from aiohttp import web

from consts import DEFAULT_CHUNK_SIZE, MEDIA_DIR


async def archive(request):
    archive_name = request.match_info.get('archive_hash', 'archive')
    archive_path = os.path.join(MEDIA_DIR, archive_name)
    if not os.path.exists(archive_path):
        raise web.HTTPNotFound(text='Архив не существует или был удален')
    response = web.StreamResponse(headers={
        'Content-Type': 'application/zip',
        'Content-Disposition': 'attachment; filename=photos.zip',
    })
    await response.prepare(request)
    process = await asyncio.subprocess.create_subprocess_exec(
        'zip', '-r', '-', '.',
        cwd=archive_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    while not process.stdout.at_eof():
        await response.write(await process.stdout.read(DEFAULT_CHUNK_SIZE))
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r', encoding='UTF-8') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, charset='UTF-8', content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
