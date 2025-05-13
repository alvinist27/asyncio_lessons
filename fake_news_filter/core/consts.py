import os
from pathlib import Path

ADAPTERS_DOMAINS = (
    'inosmi.ru',
)

ADAPTER_NOT_EXIST_URL = 'http://example.com'
INSOMNI_EXAMPLE_ARTICLE = 'https://inosmi.ru/20190629/245384784.html'
INSOMNI_NOT_EXIST_ARTICLE_URL = 'https://inosmi.ru/not/exist.html'

ARTICLES_TO_FILTER = (
    ADAPTER_NOT_EXIST_URL,
    INSOMNI_EXAMPLE_ARTICLE,
    INSOMNI_NOT_EXIST_ARTICLE_URL,
    'https://inosmi.ru/20190629/245379332.html',
    'https://inosmi.ru/20190629/245385044.html',
    'https://inosmi.ru/20190629/245382801.html',
    'https://inosmi.ru/20190629/245384728.html',
)

DEFAULT_BLACKLIST_TAGS = (
    'script',
    'time'
)

DEFAULT_UNWRAPLIST_TAGS = (
    'div',
    'p',
    'span',
    'address',
    'article',
    'header',
    'footer'
)

BASE_DIR = Path(__file__).resolve().parent.parent
CHARGED_WORDS_FILE_PATH = os.path.join(BASE_DIR, 'core', 'charged_words.txt')

ANALYZE_URLS_LIMIT_COUNT = 10
ANALYZE_URLS_LIMIT_MESSAGE = 'too many urls in request, should be 10 or less'
EMPTY_URLS_QUERY_PARAM = 'empty query parameter "urls", should be a comma separated list'
SPLIT_WORDS_TIMEOUT_SECONDS = 3
FETCH_ARTICLE_TIMEOUT_SECONDS = 5
