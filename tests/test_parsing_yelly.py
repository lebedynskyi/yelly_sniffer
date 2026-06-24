from pathlib import Path

import pytest

from scraper.parsing.sites.yelly import YellyParser

FIXTURES = Path(__file__).parent / "fixtures" / "yelly"


@pytest.fixture
def parser():
    return YellyParser()


def test_parse_metas_with_article_tags(parser):
    html = (FIXTURES / "meta_article_tags.html").read_text()

    metas = parser.parse_metas(html)

    assert [m.title for m in metas] == ["First Post", "Second Post"]
    assert metas[0].url == "https://yelly.ru/post-one"


def test_parse_metas_falls_back_to_headline_spans(parser):
    html = (FIXTURES / "meta_fallback_headline.html").read_text()

    metas = parser.parse_metas(html)

    assert [m.title for m in metas] == ["Fallback One", "Fallback Two"]
    assert metas[0].url == "https://yelly.ru/fallback-one"


def test_parse_article_extracts_title_body_url_and_image(parser):
    html = (FIXTURES / "article.html").read_text()

    article = parser.parse_article(html)

    assert article.title == "First Post"
    assert article.url == "https://yelly.ru/post-one"
    assert article.feature_image == "https://yelly.ru/img/feature.jpg"
    assert "Real paragraph one." in article.body
    assert "Real paragraph two." in article.body


def test_parse_article_strips_ads_and_tracking(parser):
    html = (FIXTURES / "article.html").read_text()

    article = parser.parse_article(html)

    assert "adsbygoogle" not in article.body
    assert "yandex-rtb" not in article.body
    assert "track()" not in article.body
