import anyio
import pymorphy2

from fake_news_filter.text_tools import calculate_jaundice_rate, split_by_words

morph = pymorphy2.MorphAnalyzer()


def test_calculate_jaundice_rate():
    assert -0.01 < calculate_jaundice_rate([], []) < 0.01
    assert 33.0 < calculate_jaundice_rate(['все', 'аутсайдер', 'побег'], ['аутсайдер', 'банкротство']) < 34.0


def test_split_by_words():
    assert anyio.run(split_by_words, morph, 'Во-первых, он хочет, чтобы') == ['во-первых', 'хотеть', 'чтобы']
    assert anyio.run(
        split_by_words,
        morph,
        '«Удивительно, но это стало началом!»',
    ) == ['удивительно', 'это', 'стать', 'начало']
