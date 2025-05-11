import pathlib

import aiohttp
import anyio
import pymorphy2
from async_timeout import timeout

from fake_news_filter.adapters import ArticleNotFound
from fake_news_filter.adapters.inosmi_ru import sanitize
from fake_news_filter.core import consts
from fake_news_filter.core.choices import ProcessingStatus
from fake_news_filter.core.consts import ARTICLES_TO_FILTER
from fake_news_filter.core.fake_rate import FakeRate
from fake_news_filter.text_tools import calculate_jaundice_rate, split_by_words


async def fetch(session, url: str):
    if not any(url.startswith(domain) for domain in consts.ADAPTERS_DOMAINS):
        raise ArticleNotFound
    try:
        async with timeout(consts.FETCH_ARTICLE_TIMEOUT_SECONDS) as timeout_obj:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
    finally:
        if timeout_obj.expired:
            raise TimeoutError


async def process_article(session, morph, charged_words, url, result):
    try:
        html = await fetch(session, url)
    except aiohttp.client_exceptions.ClientResponseError:
        result.append(FakeRate(url=url, status=ProcessingStatus.FETCH_ERROR))
        return None
    except ArticleNotFound:
        result.append(FakeRate(url=url, status=ProcessingStatus.PARSING_ERROR))
        return None
    except TimeoutError:
        result.append(FakeRate(url=url, status=ProcessingStatus.TIMEOUT))
        return None

    topic_text = sanitize(html, plaintext=True)

    article_words = split_by_words(morph=morph, text=topic_text)
    rating = calculate_jaundice_rate(article_words=article_words, charged_words=charged_words)

    result.append(FakeRate(url=url, status=ProcessingStatus.OK,  rating=rating, words_count=len(article_words)))


async def main():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = pathlib.Path(consts.CHARGED_WORDS_FILENAME).read_text().split('\n')

    results = []
    async with aiohttp.ClientSession() as session:
        async with anyio.create_task_group() as tg:
            for url in ARTICLES_TO_FILTER:
                tg.start_soon(process_article, session, morph, charged_words, url, results)
    for result in results:
        print(result)


anyio.run(main)
