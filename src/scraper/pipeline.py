import dataclasses
import logging
import random
import time
from datetime import datetime, timezone

from scraper.fetching import Fetcher
from scraper.parsing import ArticleMeta, Parser
from scraper.post_tracking import Article, ArticleStore
from scraper.publishing import facebook as facebook_publishing
from scraper.publishing import wordpress as wordpress_publishing

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class SiteHandlers:
    name: str
    url: str
    fetcher: Fetcher
    parser: Parser


def run_pipeline(
    sites: list[SiteHandlers],
    store: ArticleStore,
    sanitizer,
    fixer,
    wp_publisher,
    fb_publisher,
    do_scrape: bool,
    do_xmlrpc: bool,
    do_facebook: bool,
) -> None:
    if do_scrape:
        picked = _pick_one_article(sites, store)
        if picked is not None:
            site, meta = picked
            _process_article(site, meta, store, sanitizer, fixer)
        else:
            logger.info("No new article found across %d site(s)", len(sites))
    else:
        logger.info("Scraping disabled for this run")

    if do_xmlrpc:
        wordpress_publishing.publish_pending(store, wp_publisher)
    else:
        logger.info("WordPress publishing disabled for this run")

    if do_facebook:
        facebook_publishing.publish_pending(store, fb_publisher)
    else:
        logger.info("Facebook publishing disabled for this run")


def _pick_one_article(
    sites: list[SiteHandlers],
    store: ArticleStore,
    rng: random.Random | None = None,
) -> tuple[SiteHandlers, ArticleMeta] | None:
    shuffle = rng.shuffle if rng is not None else random.shuffle

    shuffled_sites = list(sites)
    shuffle(shuffled_sites)

    for site in shuffled_sites:
        logger.info("Checking site %s for a new article", site.name)
        try:
            listing_html = site.fetcher.fetch(site.url)
            metas = list(site.parser.parse_metas(listing_html))
        except Exception as e:
            logger.warning("Skipping site %s: %s", site.name, e)
            time.sleep(1)
            continue
        shuffle(metas)

        for meta in metas:
            if not store.exists(meta_title=meta.title, original_url=meta.url):
                return site, meta

    return None


def _process_article(
    site: SiteHandlers,
    meta: ArticleMeta,
    store: ArticleStore,
    sanitizer,
    fixer,
) -> None:
    article_html = site.fetcher.fetch(meta.url)
    parsed = site.parser.parse_article(article_html)

    sanitized_body = sanitizer.sanitize_html(parsed.body)
    fixed_body = fixer.fix_html(sanitized_body)

    store.save(
        Article(
            meta_title=meta.title,
            article_title=parsed.title,
            article_body=fixed_body,
            original_url=parsed.url or meta.url,
            discovered_at=datetime.now(timezone.utc).isoformat(),
            feature_image_url=parsed.feature_image,
        )
    )

