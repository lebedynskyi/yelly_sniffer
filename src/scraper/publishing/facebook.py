import logging
import random
import re
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.post import Post
from facebook_business.api import FacebookAdsApi

from scraper.post_tracking import Article, ArticleStore

logger = logging.getLogger(__name__)

SMALL_ARTICLE_MAX_CHARS = 5000
MEDIUM_ARTICLE_MAX_CHARS = 9000

SMALL_ARTICLE_EXCERPT_RATIO = 0.7
MEDIUM_ARTICLE_EXCERPT_RATIO = 0.5
BIG_ARTICLE_EXCERPT_RATIO = 0.3

SENTENCE_END_RE = re.compile(r"[.!?…]")

CTA_VARIANTS = [
    "Больше читай в первом комментарии 👇",
    "Продолжение истории — в первом комментарии 👇",
    "Полная версия ждёт в комментариях 👇",
    "Хочешь дочитать? Заходи в первый комментарий 👇",
    "Вся история — по ссылке в комментах 👇",
    "Вся история — по ссылке в комментарии 👇",
]


LINE_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"}

HORIZONTAL_WHITESPACE_RE = re.compile(r"[ \t]+")
NEWLINE_PADDING_RE = re.compile(r" *\n+ *")


def normalize_block_text(text: str) -> str:
    text = HORIZONTAL_WHITESPACE_RE.sub(" ", text)
    text = NEWLINE_PADDING_RE.sub("\n", text)
    return text.strip()


def strip_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for br in soup.find_all("br"):
        br.replace_with("\n")

    lines = []
    for block in soup.find_all(LINE_TAGS):
        if block.find_parent(LINE_TAGS):
            continue
        text = normalize_block_text(block.get_text(separator=" ", strip=False))
        if text:
            lines.append(text)

    if not lines:
        return normalize_block_text(soup.get_text(separator=" ", strip=False))

    return "\n\n".join(lines)


def excerpt_ratio_for(html_body: str) -> float:
    length = len(html_body)
    if length < SMALL_ARTICLE_MAX_CHARS:
        return SMALL_ARTICLE_EXCERPT_RATIO
    if length <= MEDIUM_ARTICLE_MAX_CHARS:
        return MEDIUM_ARTICLE_EXCERPT_RATIO
    return BIG_ARTICLE_EXCERPT_RATIO


def make_excerpt(html_body: str) -> str:
    text = strip_html(html_body)
    ratio = excerpt_ratio_for(html_body)
    target = int(len(text) * ratio)

    best_cut = None
    for match in SENTENCE_END_RE.finditer(text, 0, target + 1):
        best_cut = match.end()

    cut = best_cut if best_cut is not None else target
    return text[:cut].strip()


def build_post_text(article: Article) -> str:
    excerpt = make_excerpt(article.article_body)
    cta = random.choice(CTA_VARIANTS)
    return f"{excerpt}\n\n{cta}"


class FacebookPublisher(ABC):
    @abstractmethod
    def publish(self, article: Article) -> str:
        raise NotImplementedError


class GraphApiPublisher(FacebookPublisher):
    def __init__(self, page_id: str, access_token: str):
        FacebookAdsApi.init(access_token=access_token)
        self.page = Page(page_id)

    def publish(self, article: Article) -> str:
        logger.debug("Publishing to Facebook Page: %s", article.meta_title)

        result = self.page.create_photo(
            params={
                "url": article.feature_image_url,
                "message": build_post_text(article),
            }
        )
        post_id = result.get("post_id") or result["id"]

        try:
            Post(post_id).create_comment(params={"message": article.wordpress_url})
        except Exception:
            logger.exception("Failed to add link comment to Facebook post %s", post_id)

        return post_id


def publish_pending(store: ArticleStore, publisher: FacebookPublisher) -> None:
    pending = store.find_unpublished("facebook")
    if not pending:
        logger.info("No articles pending Facebook publish")
        return

    article = pending[0]
    try:
        post_id = publisher.publish(article)
    except Exception:
        logger.exception("Failed to publish article %s to Facebook", article.id)
        return

    store.mark_published(article.id, target="facebook")
    logger.info("Published article %s to Facebook as post %s", article.id, post_id)
