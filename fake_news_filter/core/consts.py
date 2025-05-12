ADAPTERS_DOMAINS = (
    'https://inosmi.ru',
)

ARTICLES_TO_FILTER = (
    'https://inosmi.ru/20190629/245384784.html',
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

CHARGED_WORDS_FILENAME = 'charged_words.txt'

SPLIT_WORDS_TIMEOUT_SECONDS = 3
FETCH_ARTICLE_TIMEOUT_SECONDS = 5
