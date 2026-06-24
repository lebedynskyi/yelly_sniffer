import random
from datetime import datetime, timezone

import pytest

from scraper.parsing import Article as ParsedArticle
from scraper.parsing import ArticleMeta
from scraper.pipeline import SiteHandlers, _pick_one_article, run_pipeline
from scraper.post_tracking import ArticleStore
from scraper.publishing.wordpress import WordpressPublishResult


@pytest.fixture
def store(tmp_path):
    return ArticleStore(tmp_path / "articles.sqlite")


def make_site_handlers(mocker, meta_title="New Post", meta_url="https://example.com/new"):
    fetcher = mocker.MagicMock()
    fetcher.fetch.side_effect = ["<html>listing</html>", "<html>article</html>"]

    parser = mocker.MagicMock()
    parser.parse_metas.return_value = [ArticleMeta(title=meta_title, url=meta_url)]
    parser.parse_article.return_value = ParsedArticle(
        title="New Post Title", body="<p>raw</p>", url=meta_url, feature_image="https://example.com/img.jpg"
    )

    return SiteHandlers(name="site1", url="https://example.com", fetcher=fetcher, parser=parser), fetcher, parser


def test_full_run_processes_new_article_through_to_publish(mocker, store):
    site, fetcher, parser = make_site_handlers(mocker)

    sanitizer = mocker.MagicMock()
    sanitizer.sanitize_html.return_value = "<p>sanitized</p>"

    fixer = mocker.MagicMock()
    fixer.fix_html.return_value = "<p>fixed</p>"

    wp_publisher = mocker.MagicMock()
    wp_publisher.publish.return_value = WordpressPublishResult(post_id=1, url="https://blog.example.com/new-post")

    fb_publisher = mocker.MagicMock()
    fb_publisher.publish.return_value = "fb-1"

    run_pipeline(
        sites=[site],
        store=store,
        sanitizer=sanitizer,
        fixer=fixer,
        wp_publisher=wp_publisher,
        fb_publisher=fb_publisher,
        do_scrape=True,
        do_xmlrpc=True,
        do_facebook=True,
    )

    fetcher.fetch.assert_any_call("https://example.com/new")
    sanitizer.sanitize_html.assert_called_once_with("<p>raw</p>")
    fixer.fix_html.assert_called_once_with("<p>sanitized</p>")
    wp_publisher.publish.assert_called_once()
    fb_publisher.publish.assert_called_once()
    assert store.find_unpublished("wordpress") == []
    assert store.find_unpublished("facebook") == []


def test_scrape_skips_already_seen_article(mocker, store):
    site, fetcher, parser = make_site_handlers(mocker, meta_title="Dup", meta_url="https://example.com/dup")
    store.save(
        __import__("scraper.post_tracking", fromlist=["Article"]).Article(
            meta_title="Dup",
            article_title="Dup",
            article_body="<p>x</p>",
            original_url="https://example.com/dup",
            discovered_at=datetime.now(timezone.utc).isoformat(),
        )
    )

    run_pipeline(
        sites=[site],
        store=store,
        sanitizer=mocker.MagicMock(),
        fixer=mocker.MagicMock(),
        wp_publisher=mocker.MagicMock(),
        fb_publisher=mocker.MagicMock(),
        do_scrape=True,
        do_xmlrpc=False,
        do_facebook=False,
    )

    parser.parse_article.assert_not_called()


def test_scrape_only_does_not_publish(mocker, store):
    site, fetcher, parser = make_site_handlers(mocker)

    wp_publisher = mocker.MagicMock()
    fb_publisher = mocker.MagicMock()

    run_pipeline(
        sites=[site],
        store=store,
        sanitizer=mocker.MagicMock(sanitize_html=mocker.MagicMock(return_value="<p>s</p>")),
        fixer=mocker.MagicMock(fix_html=mocker.MagicMock(return_value="<p>f</p>")),
        wp_publisher=wp_publisher,
        fb_publisher=fb_publisher,
        do_scrape=True,
        do_xmlrpc=False,
        do_facebook=False,
    )

    wp_publisher.publish.assert_not_called()
    fb_publisher.publish.assert_not_called()
    assert len(store.find_unpublished("wordpress")) == 1


def test_wordpress_only_publishes_without_scraping(mocker, store):
    site, fetcher, parser = make_site_handlers(mocker)
    wp_publisher = mocker.MagicMock()
    wp_publisher.publish.return_value = 1

    run_pipeline(
        sites=[site],
        store=store,
        sanitizer=mocker.MagicMock(),
        fixer=mocker.MagicMock(),
        wp_publisher=wp_publisher,
        fb_publisher=mocker.MagicMock(),
        do_scrape=False,
        do_xmlrpc=True,
        do_facebook=False,
    )

    fetcher.fetch.assert_not_called()
    parser.parse_metas.assert_not_called()
    wp_publisher.publish.assert_not_called()  # nothing saved yet, store is empty


def make_site(mocker, name, meta_title, meta_url, has_new=True):
    fetcher = mocker.MagicMock()
    fetcher.fetch.side_effect = lambda url, _meta_url=meta_url: (
        "<html>article</html>" if url == _meta_url else "<html>listing</html>"
    )

    metas = [] if not has_new else [ArticleMeta(title=meta_title, url=meta_url)]

    parser = mocker.MagicMock()
    parser.parse_metas.return_value = metas
    parser.parse_article.return_value = ParsedArticle(
        title=f"{meta_title} Title", body="<p>raw</p>", url=meta_url, feature_image=None
    )

    site = SiteHandlers(name=name, url=f"https://{name}.example.com", fetcher=fetcher, parser=parser)
    return site, fetcher, parser


def test_picks_exactly_one_article_across_multiple_sites_with_new_content(mocker, store):
    site_a, fetcher_a, parser_a = make_site(mocker, "sitea", "Post A", "https://sitea.example.com/a")
    site_b, fetcher_b, parser_b = make_site(mocker, "siteb", "Post B", "https://siteb.example.com/b")

    sanitizer = mocker.MagicMock(sanitize_html=mocker.MagicMock(return_value="<p>s</p>"))
    fixer = mocker.MagicMock(fix_html=mocker.MagicMock(return_value="<p>f</p>"))

    run_pipeline(
        sites=[site_a, site_b],
        store=store,
        sanitizer=sanitizer,
        fixer=fixer,
        wp_publisher=mocker.MagicMock(),
        fb_publisher=mocker.MagicMock(),
        do_scrape=True,
        do_xmlrpc=False,
        do_facebook=False,
    )

    assert parser_a.parse_article.call_count + parser_b.parse_article.call_count == 1
    assert len(store.find_unpublished("wordpress")) == 1


def test_picker_skips_site_with_no_new_articles(mocker, store):
    empty_site, _, parser_empty = make_site(mocker, "emptysite", "n/a", "https://emptysite.example.com/x", has_new=False)
    full_site, _, parser_full = make_site(mocker, "fullsite", "Post C", "https://fullsite.example.com/c")

    rng = random.Random(0)
    # Force empty_site to be evaluated first regardless of shuffle outcome.
    rng.shuffle = lambda seq: seq.sort(key=lambda s: 0 if s is empty_site else 1)

    picked = _pick_one_article([empty_site, full_site], store, rng=rng)

    assert picked is not None
    picked_site, picked_meta = picked
    assert picked_site is full_site
    assert picked_meta.title == "Post C"
    parser_empty.parse_article.assert_not_called()


def test_picker_returns_none_when_all_sites_exhausted(mocker, store):
    site, fetcher, parser = make_site_handlers(mocker, meta_title="Dup2", meta_url="https://example.com/dup2")
    store.save(
        __import__("scraper.post_tracking", fromlist=["Article"]).Article(
            meta_title="Dup2",
            article_title="Dup2",
            article_body="<p>x</p>",
            original_url="https://example.com/dup2",
            discovered_at=datetime.now(timezone.utc).isoformat(),
        )
    )

    picked = _pick_one_article([site], store)

    assert picked is None
    parser.parse_article.assert_not_called()


def test_picker_does_not_mutate_caller_lists(mocker, store):
    site_a, _, _ = make_site(mocker, "sitea2", "Post D", "https://sitea2.example.com/d", has_new=False)
    site_b, _, _ = make_site(mocker, "siteb2", "Post E", "https://siteb2.example.com/e", has_new=False)

    sites = [site_a, site_b]
    sites_copy = list(sites)

    _pick_one_article(sites, store, rng=random.Random(1))

    assert sites == sites_copy


def force_order(*ordered_sites):
    order = {id(site): i for i, site in enumerate(ordered_sites)}

    class _Rng:
        @staticmethod
        def shuffle(seq):
            seq.sort(key=lambda x: order.get(id(x), len(order)))

    return _Rng()


def test_picker_skips_site_whose_listing_fetch_raises(mocker, store):
    mocker.patch("scraper.pipeline.time.sleep")

    bad_site, bad_fetcher, _ = make_site(mocker, "badsite", "n/a", "https://badsite.example.com/x")
    bad_fetcher.fetch.side_effect = ConnectionError("boom")

    good_site, _, parser_good = make_site(mocker, "goodsite", "Post F", "https://goodsite.example.com/f")

    picked = _pick_one_article([bad_site, good_site], store, rng=force_order(bad_site, good_site))

    assert picked is not None
    picked_site, picked_meta = picked
    assert picked_site is good_site
    assert picked_meta.title == "Post F"
    parser_good.parse_article.assert_not_called()  # only selection ran, not processing


def test_picker_skips_site_whose_parse_metas_raises(mocker, store):
    mocker.patch("scraper.pipeline.time.sleep")

    bad_site, _, bad_parser = make_site(mocker, "badparse", "n/a", "https://badparse.example.com/x")
    bad_parser.parse_metas.side_effect = ValueError("malformed html")

    good_site, _, _ = make_site(mocker, "goodsite2", "Post G", "https://goodsite2.example.com/g")

    picked = _pick_one_article([bad_site, good_site], store, rng=force_order(bad_site, good_site))

    assert picked is not None
    picked_site, picked_meta = picked
    assert picked_site is good_site
    assert picked_meta.title == "Post G"


def test_picker_returns_none_when_every_site_raises(mocker, store):
    mocker.patch("scraper.pipeline.time.sleep")

    site_a, fetcher_a, _ = make_site(mocker, "allbad1", "n/a", "https://allbad1.example.com/x")
    fetcher_a.fetch.side_effect = ConnectionError("boom")

    site_b, fetcher_b, _ = make_site(mocker, "allbad2", "n/a", "https://allbad2.example.com/y")
    fetcher_b.fetch.side_effect = TimeoutError("timeout")

    picked = _pick_one_article([site_a, site_b], store)

    assert picked is None


def test_listing_failure_logs_warning_without_traceback(mocker, store):
    mocker.patch("scraper.pipeline.time.sleep")
    logger_mock = mocker.patch("scraper.pipeline.logger")

    bad_site, bad_fetcher, _ = make_site(mocker, "badlog", "n/a", "https://badlog.example.com/x")
    bad_fetcher.fetch.side_effect = ConnectionError("boom")

    _pick_one_article([bad_site], store)

    logger_mock.warning.assert_called_once()
    logger_mock.exception.assert_not_called()


def test_listing_failure_sleeps_one_second(mocker, store):
    sleep_mock = mocker.patch("scraper.pipeline.time.sleep")

    bad_site, bad_fetcher, _ = make_site(mocker, "badsleep", "n/a", "https://badsleep.example.com/x")
    bad_fetcher.fetch.side_effect = ConnectionError("boom")

    _pick_one_article([bad_site], store)

    sleep_mock.assert_called_once_with(1)
