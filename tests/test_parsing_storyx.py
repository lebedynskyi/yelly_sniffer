from pathlib import Path

import pytest

from scraper.parsing.sites.storyx import StoryxParser

FIXTURES = Path(__file__).parent / "fixtures" / "storyx"


@pytest.fixture
def parser():
    return StoryxParser()


def test_parse_metas(parser):
    html = (FIXTURES / "meta.html").read_text()

    metas = parser.parse_metas(html)

    assert metas[0].title == "Storyx First"
    assert metas[0].url == "https://storyx.ru/post-one"


def test_parse_article(parser):
    html = (FIXTURES / "article.html").read_text()

    article = parser.parse_article(html)

    assert article.title == "Storyx First"
    assert article.url == "https://storyx.ru/post-one"
    assert article.feature_image == "https://storyx.ru/img/feature.jpg"
    assert "Storyx real content." in article.body
    assert "junk" not in article.body
