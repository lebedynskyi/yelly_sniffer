from datetime import datetime, timezone

import pytest

from scraper.post_tracking import Article, ArticleStore


@pytest.fixture
def store(tmp_path):
    return ArticleStore(tmp_path / "articles.sqlite")


def make_article(meta_title="Title", url="https://example.com/a", **overrides):
    defaults = dict(
        meta_title=meta_title,
        article_title="Article " + meta_title,
        article_body="<p>body</p>",
        original_url=url,
        discovered_at=datetime.now(timezone.utc).isoformat(),
    )
    defaults.update(overrides)
    return Article(**defaults)


def test_save_article_persists_row(store):
    store.save(make_article())

    rows = store.find_unpublished("wordpress")
    assert len(rows) == 1
    assert rows[0].meta_title == "Title"
    assert rows[0].article_body == "<p>body</p>"


def test_exists_by_title_detects_duplicate(store):
    store.save(make_article(meta_title="Same Title", url="https://example.com/1"))

    assert store.exists(meta_title="Same Title", original_url="https://example.com/2") is True


def test_exists_by_url_detects_duplicate(store):
    store.save(make_article(meta_title="A", url="https://example.com/dup"))

    assert store.exists(meta_title="Different", original_url="https://example.com/dup") is True


def test_exists_returns_false_for_new_article(store):
    store.save(make_article(meta_title="A", url="https://example.com/1"))

    assert store.exists(meta_title="B", original_url="https://example.com/2") is False


def test_wordpress_and_facebook_status_are_independent(store):
    store.save(
        make_article(
            meta_title="A",
            url="https://example.com/1",
            feature_image_url="https://example.com/img.jpg",
        )
    )
    article = store.find_unpublished("wordpress")[0]

    store.mark_published(article.id, target="wordpress")
    store.set_wordpress_url(article.id, "https://blog.example.com/a")

    assert store.find_unpublished("wordpress") == []
    unpublished_fb = store.find_unpublished("facebook")
    assert len(unpublished_fb) == 1
    assert unpublished_fb[0].id == article.id


def test_find_unpublished_facebook_requires_wordpress_url_and_image(store):
    store.save(make_article(meta_title="B", url="https://example.com/2"))

    assert store.find_unpublished("facebook") == []


def test_find_unpublished_orders_most_recent_first(store):
    store.save(make_article(meta_title="first", url="https://example.com/1"))
    store.save(make_article(meta_title="second", url="https://example.com/2"))

    rows = store.find_unpublished("wordpress")

    assert [r.meta_title for r in rows] == ["second", "first"]


def test_find_unpublished_rejects_unknown_target(store):
    with pytest.raises(ValueError):
        store.find_unpublished("not-a-real-target")


def test_mark_published_rejects_unknown_target(store):
    store.save(make_article())
    article = store.find_unpublished("wordpress")[0]

    with pytest.raises(ValueError):
        store.mark_published(article.id, target="not-a-real-target")
