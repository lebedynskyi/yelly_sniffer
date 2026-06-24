from pathlib import Path

import pytest

from scraper.parsing.sites.dzen import DzenParser

FIXTURES = Path(__file__).parent / "fixtures" / "dzen"


@pytest.fixture
def parser():
    return DzenParser()


def test_parse_metas_with_title_div(parser):
    html = (FIXTURES / "meta.html").read_text()

    metas = parser.parse_metas(html)

    assert metas[0].title == "Dzen First"
    assert metas[0].url == "https://dzen.ru/a/post-one"


def test_parse_metas_falls_back_to_card_text_when_no_title_div(parser):
    html = (FIXTURES / "meta.html").read_text()

    metas = parser.parse_metas(html)

    assert metas[1].title == "No title div fallback text"
    assert metas[1].url == "https://dzen.ru/a/post-two"


def test_parse_article(parser):
    html = (FIXTURES / "article.html").read_text()

    article = parser.parse_article(html)

    assert article.title == "Dzen First"
    assert article.url == "https://dzen.ru/a/post-one"
    assert article.feature_image == "https://dzen.ru/img/feature.jpg"
    assert "Dzen real content." in article.body
    assert "related link" not in article.body
    assert "embed junk" not in article.body
