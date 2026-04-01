import dataclasses

import logging
import random
from typing import Optional
from datetime import datetime

from src.ai.ai_fixer import LLMFixer, GeminiFixer
from src.core.cli import ParsedArgs
from src.crawl import Crawler
from src.data import SQLiteDatabase, DBArticle
from src.parser import ParserMetaResult
from src.sanitizer import Bs4HtmlSanitizer
from src.xml_rpc import WordpressRpcApi

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class PreparedArticle:
    meta_title: str
    article_title: str
    body: str
    url: str


class Updater:
    def __init__(self, database: SQLiteDatabase, crawler: Crawler, sanitizer: Bs4HtmlSanitizer,
                 fixer: GeminiFixer, xml_rpc: WordpressRpcApi):
        self.xml_rpc = xml_rpc
        self.database = database
        self.fixer = fixer
        self.sanitizer = sanitizer
        self.crawler = crawler

    def process(self, args: ParsedArgs, repeat_count=1):
        sites = args.sites
        logger.info(f"💾Processing next sites: {sites}")

        for i in range(0, args.count):
            logger.info(f"Processing number {i + 1}")

            if sites:
                self._process_sites(sites, repeat_count)
            else:
                logger.info("💾No sites provided in arguments")

            xmlrpc = args.xmlrpc
            if xmlrpc:
                self._publish_saved_articles()
            else:
                logger.info("💾No xmlrpc enabled")

            facebook = args.facebook
            if facebook:
                self._publish_facebook_post()
            else:
                logger.info("💾No facebook enabled")

    def _process_sites(self, sites: list[str], repeat_count: int) -> bool:
        for i in range(0, repeat_count):
            site = random.choice(sites)
            try:
                logger.info(f"💾Processing site {site}. Attempt {i}")

                metas = self.crawler.crawl_meta(site)
                prepared = self._process_metas(metas)
                if prepared:
                    db_article = DBArticle(
                        prepared.meta_title, prepared.article_title, prepared.body, prepared.url,
                        datetime.now().isoformat()
                    )
                    self.database.save_article(db_article)
                    return True
                else:
                    logger.info("No new articles saved")
            except BaseException as e:
                # logger.warning(f"Failed to process site {site}, {e}")
                logger.exception(f"💾Failed to process site {site}, %s", e)

        return False

    def _process_metas(self, metas: list[ParserMetaResult]) -> Optional[PreparedArticle]:
        for m in metas:
            if not self.database.exist_meta(m.title):
                article = self.crawler.crawl_article(m)
                sanitized_html = self.sanitizer.sanitize_html(article.body)
                repaired_html = self.fixer.fix_broken_html(sanitized_html)
                prepared_article = PreparedArticle(m.title, article.title, repaired_html, m.url)
                return prepared_article

        return None

    def _publish_saved_articles(self):
        logger.info("💾xmlrpc is enabled. Publish articles")
        posts = self.database.find_by_rpc_status(status=False)
        if posts:
            post = posts[0]
            logger.info(f"💾xmlrpc publishing: {post.meta_title}")
            self.xml_rpc.publish(post)
            self.database.update_rpc(post.id, status=True)
        else:
            logger.info("💾Publishing is up to date")

    def _publish_facebook_post(self):
        logger.info("💾facebook is enabled. Publish articles")
        pass
