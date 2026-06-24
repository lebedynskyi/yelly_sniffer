from datetime import datetime, timezone

import pytest

from scraper.post_tracking import Article, ArticleStore
from scraper.publishing.facebook import (
    CTA_VARIANTS,
    FacebookPublisher,
    GraphApiPublisher,
    build_post_text,
    excerpt_ratio_for,
    make_excerpt,
    publish_pending,
    strip_html,
)


@pytest.fixture
def store(tmp_path):
    return ArticleStore(tmp_path / "articles.sqlite")


def make_article(title="Title", url="https://example.com/a", **overrides):
    defaults = dict(
        meta_title=title,
        article_title=title,
        article_body="<p>body</p>",
        original_url=url,
        discovered_at=datetime.now(timezone.utc).isoformat(),
        wordpress_url="https://blog.example.com/article",
        feature_image_url="https://example.com/image.jpg",
    )
    defaults.update(overrides)
    return Article(**defaults)


def test_graph_api_publisher_is_facebook_publisher():
    assert issubclass(GraphApiPublisher, FacebookPublisher)


def test_publish_calls_graph_api_with_image_and_text(mocker):
    fake_api_init = mocker.patch("scraper.publishing.facebook.FacebookAdsApi.init")
    fake_page_cls = mocker.patch("scraper.publishing.facebook.Page")
    fake_page = fake_page_cls.return_value
    fake_page.create_photo.return_value = {"id": "123_456", "post_id": "123_456"}
    fake_post_cls = mocker.patch("scraper.publishing.facebook.Post")

    publisher = GraphApiPublisher(page_id="123", access_token="token-abc")
    article = make_article(url="https://example.com/article")

    post_id = publisher.publish(article)

    assert post_id == "123_456"
    fake_api_init.assert_called_once_with(access_token="token-abc")
    fake_page_cls.assert_called_once_with("123")
    _, kwargs = fake_page.create_photo.call_args
    assert kwargs["params"]["url"] == article.feature_image_url
    assert any(cta in kwargs["params"]["message"] for cta in CTA_VARIANTS)
    fake_post_cls.assert_called_once_with("123_456")
    fake_post_cls.return_value.create_comment.assert_called_once_with(
        params={"message": article.wordpress_url}
    )


def test_publish_swallows_comment_failure(mocker):
    mocker.patch("scraper.publishing.facebook.FacebookAdsApi.init")
    fake_page_cls = mocker.patch("scraper.publishing.facebook.Page")
    fake_page_cls.return_value.create_photo.return_value = {"id": "1"}
    fake_post_cls = mocker.patch("scraper.publishing.facebook.Post")
    fake_post_cls.return_value.create_comment.side_effect = RuntimeError("comment failed")

    publisher = GraphApiPublisher(page_id="123", access_token="token-abc")
    post_id = publisher.publish(make_article())

    assert post_id == "1"


def test_publish_no_browser_or_session_files_touched(mocker):
    mocker.patch("scraper.publishing.facebook.FacebookAdsApi.init")
    fake_page_cls = mocker.patch("scraper.publishing.facebook.Page")
    fake_page_cls.return_value.create_photo.return_value = {"id": "1"}
    mocker.patch("scraper.publishing.facebook.Post")

    import scraper.publishing.facebook as fb_module

    assert not hasattr(fb_module, "webdriver")
    assert "selenium" not in fb_module.__file__


def test_publish_pending_marks_published_on_success(mocker, store):
    store.save(make_article())
    article = store.find_unpublished("facebook")[0]

    fake_publisher = mocker.MagicMock()
    fake_publisher.publish.return_value = "post-1"

    publish_pending(store, fake_publisher)

    assert store.find_unpublished("facebook") == []
    fake_publisher.publish.assert_called_once_with(article)


def test_publish_pending_leaves_status_unchanged_on_failure(mocker, store):
    store.save(make_article())

    fake_publisher = mocker.MagicMock()
    fake_publisher.publish.side_effect = RuntimeError("graph api down")

    publish_pending(store, fake_publisher)

    assert len(store.find_unpublished("facebook")) == 1


def test_find_unpublished_excludes_articles_without_wordpress_url(store):
    store.save(make_article(wordpress_url=None))

    assert store.find_unpublished("facebook") == []


def test_find_unpublished_excludes_articles_without_feature_image(store):
    store.save(make_article(feature_image_url=None))

    assert store.find_unpublished("facebook") == []


def test_strip_html_removes_tags():
    assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"


def test_excerpt_ratio_for_small_medium_big():
    assert excerpt_ratio_for("x" * 4999) == 0.7
    assert excerpt_ratio_for("x" * 5000) == 0.5
    assert excerpt_ratio_for("x" * 9000) == 0.5
    assert excerpt_ratio_for("x" * 9001) == 0.3


def test_make_excerpt_cuts_at_nearest_sentence_boundary():
    body = "<p>First sentence here. Second sentence here. Third sentence here. Fourth.</p>"
    excerpt = make_excerpt(body)

    assert excerpt.endswith((".", "!", "?", "…"))
    assert excerpt in strip_html(body)


def test_make_excerpt_hard_cuts_when_no_sentence_boundary():
    body = "<p>" + ("word " * 200) + "</p>"
    excerpt = make_excerpt(body)

    text = strip_html(body)
    ratio = excerpt_ratio_for(body)
    assert excerpt == text[: int(len(text) * ratio)].strip()


def test_build_post_text_appends_one_of_the_cta_variants():
    article = make_article()
    text = build_post_text(article)

    assert any(text.endswith(cta) for cta in CTA_VARIANTS)
    assert "\n\n" in text
