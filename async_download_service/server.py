import argparse
import asyncio
import logging
import os

import aiofiles
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger()


async def archive(request):
    archive_name = request.match_info.get('archive_hash', 'archive')
    archive_path = os.path.join(request.app['media_dir'], archive_name)
    if not os.path.exists(archive_path):
        raise web.HTTPNotFound(text='Archive not found')
    response = web.StreamResponse(headers={
        'Content-Type': 'application/zip',
        'Content-Disposition': 'attachment; filename=photos.zip',
    })
    response.enable_chunked_encoding(request.app['chunk_size'])
    await response.prepare(request)
    process = await asyncio.subprocess.create_subprocess_exec(
        'zip', '-r', '-', '.',
        cwd=archive_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        while not process.stdout.at_eof():
            logger.info('Sending archive chunk ...')
            await response.write(await process.stdout.read(request.app['chunk_size']))
            await asyncio.sleep(request.app['response_delay'])
    except asyncio.CancelledError as error:
        logger.info('Download was interrupted')
        process.kill()
        raise error
    else:
        logger.info('Download was completed')
    finally:
        await process.communicate()
        response.force_close()
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r', encoding='UTF-8') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, charset='UTF-8', content_type='text/html')


def configure_application(application):
    parser = argparse.ArgumentParser()
    parser.add_argument('--enable_logging', default=True, help='enable console logging', action='store_true')
    parser.add_argument('--response_delay', default=0, help='set delay in seconds between chunks sending')
    parser.add_argument('--media_dir', default='src_photos', help='set path for photos dir')
    parser.add_argument('--chunk_size', default=10000, help='an integer for chunk size')

    parser_args = parser.parse_args()
    application['response_delay'] = int(os.getenv('response_delay', parser_args.response_delay))
    application['media_dir'] = os.getenv('media_dir', parser_args.media_dir)
    application['chunk_size'] = int(os.getenv('chunk_size', parser_args.chunk_size))
    application['enable_logging'] = os.getenv('enable_logging', parser_args.enable_logging).lower() == 'true'
    if application['enable_logging']:
        logging.basicConfig(level=logging.INFO)


if __name__ == '__main__':
    app = web.Application()
    configure_application(application=app)
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
