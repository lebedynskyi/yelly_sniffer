import logging
from collections.abc import Iterable

from src.api.yelly import YellyApi

logger = logging.getLogger(__name__)


class DatabaseUpdater:
    def __init__(self, database, yelly: YellyApi, config):
        self.config = config
        self.yelly = yelly
        self.database = database

    def process_sites(self, sites):
        logger.info("Fetching metadata for sites '%s'", sites)
        page_urls = [self.yelly.get_page_link(s, 0) for s in sites]
        self.process_pages(page_urls)

    def process_pages(self, pages):
        logger.info("Fetching metadata for pages '%s'", pages)
        post_metas = []
        for page in pages:
            for meta in self.yelly.get_posts_meta(page):
                post_metas.append(meta)

        # TODO redesign to work page by page ??
        logger.info("Updater fetched %s titles for pages '%s'", len(post_metas), pages)
        count = self._check_update(post_metas)
        if count > 0:
            logger.info("Updater saved %s new titles", count)
        else:
            logger.info("Updater everything is up to date")

    def process_links(self, links):
        if not isinstance(links, Iterable):
            links = [links]

        count = 0
        for link in links:
            content = self.yelly.get_post_content(link)
            if not self.database.exist(content.title):
                self.database.insert_new_post(content)
                count = count + 1

        return count

    def _check_update(self, post_metas):
        count = 0
        for meta in post_metas:
            if not self.database.exist(meta.title):
                logger.info("Fetch %s", meta.url)
                content = self.yelly.get_post_content(meta.url)
                self.database.insert_new_post(content)
                count = count + 1

        return count
