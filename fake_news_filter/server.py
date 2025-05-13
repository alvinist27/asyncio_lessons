from http import HTTPStatus

import pymorphy2 as pymorphy2
from aiohttp import web

from fake_news_filter.core import consts
from fake_news_filter.analyze import analyze_article_urls

morph = pymorphy2.MorphAnalyzer()


async def analyze_articles(request: web.Request) -> web.Response:
    urls = request.query.get('urls', '')
    if not urls:
        return web.json_response({'error': consts.EMPTY_URLS_QUERY_PARAM}, status=HTTPStatus.BAD_REQUEST)
    split_urls = urls.split(',')
    if len(split_urls) > consts.ANALYZE_URLS_LIMIT_COUNT:
        return web.json_response({'error': consts.ANALYZE_URLS_LIMIT_MESSAGE}, status=HTTPStatus.BAD_REQUEST)
    results = await analyze_article_urls(morph=morph, urls=split_urls)
    return web.json_response(results)


app = web.Application()
app.add_routes([
    web.get('/', analyze_articles),
])


if __name__ == '__main__':
    web.run_app(app)
