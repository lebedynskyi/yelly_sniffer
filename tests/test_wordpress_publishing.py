from datetime import datetime, timezone

import pytest

from scraper.post_tracking import Article, ArticleStore
from scraper.publishing.wordpress import WordpressPublishResult, WordpressRpcPublisher, publish_pending


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
    )
    defaults.update(overrides)
    return Article(**defaults)


def test_publish_creates_post_as_published_and_fetches_url(mocker):
    fake_client_cls = mocker.patch("scraper.publishing.wordpress.Client")
    fake_client = fake_client_cls.return_value
    fake_fetched_post = mocker.MagicMock(link="https://blog.example.com/my-post")
    fake_client.call.side_effect = [42, fake_fetched_post]

    publisher = WordpressRpcPublisher(rpc_url="https://x.com/xmlrpc.php", rpc_user="u", rpc_password="p")
    article = make_article()

    result = publisher.publish(article)

    assert result == WordpressPublishResult(post_id=42, url="https://blog.example.com/my-post")
    fake_client_cls.assert_called_once_with("https://x.com/xmlrpc.php", "u", "p")
    new_post_call = fake_client.call.call_args_list[0][0][0]
    assert new_post_call.content.post_status == "publish"
    assert new_post_call.content.title == article.article_title
    assert new_post_call.content.content == article.article_body


def test_publish_leaves_url_none_when_get_post_fails(mocker):
    fake_client_cls = mocker.patch("scraper.publishing.wordpress.Client")
    fake_client = fake_client_cls.return_value
    fake_client.call.side_effect = [42, RuntimeError("getPost failed")]

    publisher = WordpressRpcPublisher(rpc_url="https://x.com/xmlrpc.php", rpc_user="u", rpc_password="p")
    article = make_article()

    result = publisher.publish(article)

    assert result == WordpressPublishResult(post_id=42, url=None)


def test_publish_pending_marks_article_published_on_success(mocker, store):
    store.save(make_article())
    article = store.find_unpublished("wordpress")[0]

    fake_publisher = mocker.MagicMock()
    fake_publisher.publish.return_value = WordpressPublishResult(post_id=99, url="https://blog.example.com/p")

    publish_pending(store, fake_publisher)

    assert store.find_unpublished("wordpress") == []
    fake_publisher.publish.assert_called_once_with(article)
    saved = store.connection.execute("SELECT wordpress_url FROM articles WHERE id = ?", (article.id,)).fetchone()
    assert saved["wordpress_url"] == "https://blog.example.com/p"


def test_publish_pending_leaves_status_unchanged_on_failure(mocker, store):
    store.save(make_article())

    fake_publisher = mocker.MagicMock()
    fake_publisher.publish.side_effect = RuntimeError("xmlrpc down")

    publish_pending(store, fake_publisher)

    assert len(store.find_unpublished("wordpress")) == 1


def test_publish_pending_does_nothing_when_no_pending_articles(store):
    class StubPublisher:
        def publish(self, article):
            raise AssertionError("should not be called when nothing pending")

    publish_pending(store, StubPublisher())


def test_publish_uploads_feature_image_and_sets_thumbnail(mocker):
    fake_response = mocker.MagicMock(content=b"bytes", headers={"Content-Type": "image/jpeg"})
    fake_response.raise_for_status.return_value = None
    mocker.patch("scraper.publishing.wordpress.requests.get", return_value=fake_response)

    fake_client_cls = mocker.patch("scraper.publishing.wordpress.Client")
    fake_client = fake_client_cls.return_value
    fake_fetched_post = mocker.MagicMock(link="https://blog.example.com/my-post")
    fake_client.call.side_effect = [{"id": 7}, 42, fake_fetched_post]

    publisher = WordpressRpcPublisher(rpc_url="https://x.com/xmlrpc.php", rpc_user="u", rpc_password="p")
    article = make_article(feature_image_url="https://cdn.example.com/img.jpg")

    result = publisher.publish(article)

    assert result == WordpressPublishResult(post_id=42, url="https://blog.example.com/my-post")
    new_post_call = fake_client.call.call_args_list[1][0][0]
    assert new_post_call.content.thumbnail == 7


def test_publish_without_feature_image_skips_upload(mocker):
    fake_get = mocker.patch("scraper.publishing.wordpress.requests.get")
    fake_client_cls = mocker.patch("scraper.publishing.wordpress.Client")
    fake_client = fake_client_cls.return_value
    fake_fetched_post = mocker.MagicMock(link="https://blog.example.com/my-post")
    fake_client.call.side_effect = [42, fake_fetched_post]

    publisher = WordpressRpcPublisher(rpc_url="https://x.com/xmlrpc.php", rpc_user="u", rpc_password="p")
    article = make_article(feature_image_url=None)

    result = publisher.publish(article)

    fake_get.assert_not_called()
    new_post_call = fake_client.call.call_args_list[0][0][0]
    assert not hasattr(new_post_call.content, "thumbnail")
    assert result == WordpressPublishResult(post_id=42, url="https://blog.example.com/my-post")


def test_publish_continues_without_thumbnail_when_image_download_fails(mocker):
    mocker.patch(
        "scraper.publishing.wordpress.requests.get", side_effect=RuntimeError("download failed")
    )
    fake_client_cls = mocker.patch("scraper.publishing.wordpress.Client")
    fake_client = fake_client_cls.return_value
    fake_fetched_post = mocker.MagicMock(link="https://blog.example.com/my-post")
    fake_client.call.side_effect = [42, fake_fetched_post]

    publisher = WordpressRpcPublisher(rpc_url="https://x.com/xmlrpc.php", rpc_user="u", rpc_password="p")
    article = make_article(feature_image_url="https://cdn.example.com/img.jpg")

    result = publisher.publish(article)

    new_post_call = fake_client.call.call_args_list[0][0][0]
    assert not hasattr(new_post_call.content, "thumbnail")
    assert result == WordpressPublishResult(post_id=42, url="https://blog.example.com/my-post")


def test_publish_continues_without_thumbnail_when_upload_fails(mocker):
    fake_response = mocker.MagicMock(content=b"bytes", headers={"Content-Type": "image/jpeg"})
    fake_response.raise_for_status.return_value = None
    mocker.patch("scraper.publishing.wordpress.requests.get", return_value=fake_response)

    fake_client_cls = mocker.patch("scraper.publishing.wordpress.Client")
    fake_client = fake_client_cls.return_value
    fake_fetched_post = mocker.MagicMock(link="https://blog.example.com/my-post")
    fake_client.call.side_effect = [RuntimeError("uploadFile failed"), 42, fake_fetched_post]

    publisher = WordpressRpcPublisher(rpc_url="https://x.com/xmlrpc.php", rpc_user="u", rpc_password="p")
    article = make_article(feature_image_url="https://cdn.example.com/img.jpg")

    result = publisher.publish(article)

    new_post_call = fake_client.call.call_args_list[1][0][0]
    assert not hasattr(new_post_call.content, "thumbnail")
    assert result == WordpressPublishResult(post_id=42, url="https://blog.example.com/my-post")


def test_publish_falls_back_to_extension_guess_when_content_type_generic(mocker):
    fake_response = mocker.MagicMock(
        content=b"bytes", headers={"Content-Type": "application/octet-stream"}
    )
    fake_response.raise_for_status.return_value = None
    mocker.patch("scraper.publishing.wordpress.requests.get", return_value=fake_response)

    fake_client_cls = mocker.patch("scraper.publishing.wordpress.Client")
    fake_client = fake_client_cls.return_value
    fake_fetched_post = mocker.MagicMock(link="https://blog.example.com/my-post")
    fake_client.call.side_effect = [{"id": 7}, 42, fake_fetched_post]

    publisher = WordpressRpcPublisher(rpc_url="https://x.com/xmlrpc.php", rpc_user="u", rpc_password="p")
    article = make_article(feature_image_url="https://cdn.example.com/img.png")

    publisher.publish(article)

    upload_call = fake_client.call.call_args_list[0][0][0]
    assert upload_call.data["type"] == "image/png"
