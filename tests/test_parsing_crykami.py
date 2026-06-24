from pathlib import Path

import pytest

from scraper.parsing.sites.crykami import CrykamiParser

FIXTURES = Path(__file__).parent / "fixtures" / "crykami"


@pytest.fixture
def parser():
    return CrykamiParser()


def test_parse_metas(parser):
    html = (FIXTURES / "meta.html").read_text()

    metas = parser.parse_metas(html)

    assert [m.title for m in metas] == ["Crykami First", "Crykami Second"]
    assert metas[0].url == "https://crykami.com/post-one"


def test_parse_metas_empty_when_no_articles(parser):
    assert parser.parse_metas("<html><body>nothing here</body></html>") == []


def test_parse_article(parser):
    html = (FIXTURES / "article.html").read_text()

    article = parser.parse_article(html)

    assert article.title == "Crykami First"
    assert article.url == "https://crykami.com/post-one"
    assert article.feature_image == "https://crykami.com/img/feature.jpg"
    assert "Crykami real content." in article.body
    assert "adsbygoogle" not in article.body
    assert "<style>" not in article.body
