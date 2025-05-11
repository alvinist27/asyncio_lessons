from dataclasses import dataclass

from fake_news_filter.core.choices import ProcessingStatus


@dataclass(frozen=True, kw_only=True, slots=True)
class FakeRate:
    url: str
    status: ProcessingStatus
    rating: float | None = None
    words_count: int | None = None

    def __str__(self):
        return f'URL: {self.url}\nСтатус: {self.status}\nРейтинг: {self.rating}\nСлов в статье: {self.words_count}\n\n'
