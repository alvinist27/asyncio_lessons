from functools import partial
from http import HTTPStatus
from typing import Callable

import pymorphy2 as pymorphy2
from aiohttp import web

from fake_news_filter.analyze import analyze_article_urls
from fake_news_filter.core import consts


async def analyze_articles(
    request: web.Request,
    morph: pymorphy2.MorphAnalyzer,
    analyze_article_urls_func: Callable,
    analyze_urls_limit_count: int,
    analyze_urls_limit_message: str,
    empty_urls_message: str,
) -> web.Response:
    urls = request.query.get('urls', '')
    if not urls:
        return web.json_response({'error': empty_urls_message}, status=HTTPStatus.BAD_REQUEST)
    split_urls = urls.split(',')
    if len(split_urls) > analyze_urls_limit_count:
        return web.json_response({'error': analyze_urls_limit_message}, status=HTTPStatus.BAD_REQUEST)
    results = await analyze_article_urls_func(morph=morph, urls=split_urls)
    return web.json_response(results)


def main() -> None:
    morph = pymorphy2.MorphAnalyzer()
    analyze_articles_handler = partial(
        analyze_articles,
        morph=morph,
        analyze_article_urls_func=analyze_article_urls,
        analyze_urls_limit_count=consts.ANALYZE_URLS_LIMIT_COUNT,
        analyze_urls_limit_message=consts.ANALYZE_URLS_LIMIT_MESSAGE,
        empty_urls_message=consts.EMPTY_URLS_QUERY_PARAM,
    )
    app = web.Application()
    app.add_routes([web.get('/', analyze_articles_handler)])
    web.run_app(app)


if __name__ == '__main__':
    main()
