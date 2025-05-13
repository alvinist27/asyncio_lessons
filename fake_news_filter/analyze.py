import logging
import pathlib
from dataclasses import asdict

import aiohttp
import anyio
import pymorphy2
from async_timeout import timeout

from fake_news_filter.adapters import ArticleNotFound
from fake_news_filter.adapters.inosmi_ru import sanitize
from fake_news_filter.core import consts
from fake_news_filter.core.choices import ProcessingStatus
from fake_news_filter.core.fake_rate import FakeRate
from fake_news_filter.core.time_counter import count_time
from fake_news_filter.text_tools import calculate_jaundice_rate, split_by_words

logger = logging.getLogger('root')
logging.basicConfig(level=logging.INFO)


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    if not any(domain in url for domain in consts.ADAPTERS_DOMAINS):
        raise ArticleNotFound
    try:
        async with timeout(consts.FETCH_ARTICLE_TIMEOUT_SECONDS) as timeout_obj:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
    finally:
        if timeout_obj.expired:
            raise TimeoutError


async def process_article(
    session: aiohttp.ClientSession,
    morph: pymorphy2.MorphAnalyzer,
    charged_words: list[str],
    url: str,
    result: list[dict],
) -> None:
    with count_time():
        try:
            html = await fetch(session, url)
        except aiohttp.client_exceptions.ClientResponseError:
            result.append(asdict(FakeRate(url=url, status=ProcessingStatus.FETCH_ERROR.value)))
            return None
        except ArticleNotFound:
            result.append(asdict(FakeRate(url=url, status=ProcessingStatus.PARSING_ERROR.value)))
            return None
        except TimeoutError:
            result.append(asdict(FakeRate(url=url, status=ProcessingStatus.TIMEOUT.value)))
            return None

        topic_text = sanitize(html, plaintext=True)
        try:
            article_words = await split_by_words(morph=morph, text=topic_text)
        except TimeoutError:
            result.append(asdict(FakeRate(url=url, status=ProcessingStatus.TIMEOUT.value)))
            return None

        rating = calculate_jaundice_rate(article_words=article_words, charged_words=charged_words)
        result.append(
            asdict(
                FakeRate(url=url, status=ProcessingStatus.OK.value,  rating=rating, words_count=len(article_words))
            ),
        )


async def analyze_article_urls(morph: pymorphy2.MorphAnalyzer, urls: list) -> list[dict]:
    logger.info(f'Analyze for {len(urls)} urls is started')
    charged_words = pathlib.Path(consts.CHARGED_WORDS_FILE_PATH).read_text().split('\n')

    results = []
    async with aiohttp.ClientSession() as session:
        async with anyio.create_task_group() as tg:
            for url in urls:
                tg.start_soon(process_article, session, morph, charged_words, url, results)

    logger.info(f'Analyze for {len(urls)} urls is finished:')
    for result in results:
        logger.info(result)

    return results


if __name__ == '__main__':
    anyio.run(analyze_article_urls, pymorphy2.MorphAnalyzer(), consts.ARTICLES_TO_FILTER)
