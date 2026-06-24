from pathlib import Path

import pytest

from scraper.parsing.sites.happytimes import HappyTimesParser

FIXTURES = Path(__file__).parent / "fixtures" / "happytimes"


@pytest.fixture
def parser():
    return HappyTimesParser()


def test_parse_metas(parser):
    html = (FIXTURES / "meta.html").read_text()

    metas = parser.parse_metas(html)

    assert [m.title for m in metas] == ["Happy First", "Happy Second"]
    assert metas[0].url == "https://happytimes.info/post-one"


def test_parse_article(parser):
    html = (FIXTURES / "article.html").read_text()

    article = parser.parse_article(html)

    assert article.title == "Happy First"
    assert article.url == "https://happytimes.info/post-one"
    assert article.feature_image == "https://happytimes.info/img/feature.jpg"
    assert "Happy real content." in article.body
    assert "afw" not in article.body
    assert "affiliate widget" not in article.body
    assert "banner" not in article.body
