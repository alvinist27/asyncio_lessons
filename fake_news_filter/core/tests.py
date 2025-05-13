import pathlib
from typing import Iterable
from unittest.mock import patch

import aiohttp
import anyio
import pymorphy2
import pytest

from fake_news_filter.analyze import process_article
from fake_news_filter.core import consts
from fake_news_filter.core.choices import ProcessingStatus
from fake_news_filter.text_tools import calculate_jaundice_rate, split_by_words

morph = pymorphy2.MorphAnalyzer()


def test_calculate_jaundice_rate() -> None:
    assert -0.01 < calculate_jaundice_rate([], []) < 0.01
    assert 33.0 < calculate_jaundice_rate(['все', 'аутсайдер', 'побег'], ['аутсайдер', 'банкротство']) < 34.0


def test_split_by_words() -> None:
    assert anyio.run(split_by_words, morph, 'Во-первых, он хочет, чтобы') == ['во-первых', 'хотеть', 'чтобы']
    assert anyio.run(
        split_by_words,
        morph,
        '«Удивительно, но это стало началом!»',
    ) == ['удивительно', 'это', 'стать', 'начало']


async def run_process_articles(urls: Iterable, results: list) -> None:
    charged_words = pathlib.Path(consts.CHARGED_WORDS_FILE_PATH).read_text().split('\n')
    async with aiohttp.ClientSession() as session:
        for url in urls:
            await process_article(session, morph, charged_words, url, results)


@pytest.mark.parametrize('urls, error_status', [
    ((consts.INSOMNI_NOT_EXIST_ARTICLE_URL,), ProcessingStatus.FETCH_ERROR.value),
    ((consts.ADAPTER_NOT_EXIST_URL,), ProcessingStatus.PARSING_ERROR.value),
])
def test_article_urls_errors(urls, error_status):
    results = []
    anyio.run(run_process_articles, urls, results)
    assert results[-1]['status'] == error_status


@patch('fake_news_filter.core.consts.FETCH_ARTICLE_TIMEOUT_SECONDS', 0)
def test_article_fetch_timeout():
    results = []
    anyio.run(run_process_articles, (consts.INSOMNI_EXAMPLE_ARTICLE,), results)
    assert results[-1]['status'] == ProcessingStatus.TIMEOUT.value


@patch('fake_news_filter.core.consts.SPLIT_WORDS_TIMEOUT_SECONDS', 0)
def test_split_words_timeout():
    results = []
    anyio.run(run_process_articles, (consts.INSOMNI_EXAMPLE_ARTICLE,), results)
    assert results[-1]['status'] == ProcessingStatus.TIMEOUT.value
