import logging
import mimetypes
from typing import NamedTuple, Optional
from xmlrpc.client import Binary

import requests
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import posts as wp_posts_api
from wordpress_xmlrpc.methods.media import UploadFile

from scraper.post_tracking import Article, ArticleStore

logger = logging.getLogger(__name__)

GENERIC_CONTENT_TYPES = {"", "application/octet-stream"}


class WordpressPublishResult(NamedTuple):
    post_id: int
    url: Optional[str]


class WordpressRpcPublisher:
    def __init__(self, rpc_url: str, rpc_user: str, rpc_password: str):
        self.client = Client(rpc_url, rpc_user, rpc_password)

    def publish(self, article: Article) -> WordpressPublishResult:
        logger.debug("Publishing to WordPress: %s", article.meta_title)

        post = WordPressPost()
        post.title = article.article_title
        post.content = article.article_body
        post.post_status = "publish"

        if article.feature_image_url:
            try:
                response = requests.get(article.feature_image_url)
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
                if content_type in GENERIC_CONTENT_TYPES:
                    guessed, _ = mimetypes.guess_type(article.feature_image_url)
                    content_type = guessed or "application/octet-stream"
                filename = article.feature_image_url.rsplit("/", 1)[-1] or "feature-image"
                if "." not in filename:
                    ext = mimetypes.guess_extension(content_type) or ".jpg"
                    filename += ext
                upload = self.client.call(
                    UploadFile(
                        {"name": filename, "type": content_type, "bits": Binary(response.content)}
                    )
                )
                post.thumbnail = upload["id"]
            except Exception:
                logger.exception(
                    "Failed to upload feature image %s, publishing without one",
                    article.feature_image_url,
                )

        post_id = self.client.call(wp_posts_api.NewPost(post))

        url = None
        try:
            fetched = self.client.call(wp_posts_api.GetPost(post_id))
            url = fetched.link or None
        except Exception:
            logger.exception("Failed to fetch live URL for WordPress post %s", post_id)

        return WordpressPublishResult(post_id=post_id, url=url)


def publish_pending(store: ArticleStore, publisher: WordpressRpcPublisher) -> None:
    pending = store.find_unpublished("wordpress")
    if not pending:
        logger.info("No articles pending WordPress publish")
        return

    article = pending[0]
    try:
        result = publisher.publish(article)
    except Exception:
        logger.exception("Failed to publish article %s to WordPress", article.id)
        return

    if result.url:
        store.set_wordpress_url(article.id, result.url)
    else:
        logger.warning("No live URL captured for article %s, post %s", article.id, result.post_id)

    store.mark_published(article.id, target="wordpress")
    logger.info("Published article %s to WordPress as post %s", article.id, result.post_id)
