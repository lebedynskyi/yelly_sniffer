import logging
import random
import urllib
from collections.abc import Iterable

from src.api.parsers import CrykamiParser, YellyParser, HappyTimesParser, DzenRuParser

logger = logging.getLogger(__name__)

DB_UPDATE_COUNT = 2

_parsers = {
    "cpykami.ru": CrykamiParser(),
    "happytimes.info": HappyTimesParser(),
    "dzen.ru": DzenRuParser()
}


def get_parser_for_site(site):
    parser = YellyParser()
    try:
        key = urllib.parse.urlparse(site).netloc
        if key in _parsers.keys():
            parser = _parsers[key]

    except BaseException as e:
        logger.exception("Unable to parse site %s. Yelly will be used" % site, e)

    return parser


class DatabaseUpdater:
    def __init__(self, database, config):
        self.config = config
        self.database = database

    def process_sites(self, sites):
        if not isinstance(sites, Iterable):
            sites = [sites]

        sites = [random.choice(sites)]

        logger.info("Fetching metadata for sites '%s'", sites)
        post_metas = []
        for s in sites:
            parser = get_parser_for_site(s)
            for meta in parser.get_posts_meta(s):
                post_metas.append(meta)

        logger.info("Fetched %s metas for sites %s", len(post_metas), sites)
        random.shuffle(post_metas)

        count = self._check_update(post_metas)
        if count > 0:
            logger.info("Updater saved %s new titles", count)
        else:
            logger.info("Updater everything is up to date")
        return count

    def process_links(self, links):
        if not isinstance(links, Iterable):
            links = [links]

        count = 0
        for link in links:
            parser = get_parser_for_site(link)
            content = parser.get_post_content(link)
            if not self.database.exist(content.title):
                self.database.insert_new_post(content)
                count = count + 1

        if count > 0:
            logger.info("Updater saved %s new titles", count)
        else:
            logger.info("Updater everything is up to date")
        return count

    def _check_update(self, post_metas):
        count = 0
        for meta in post_metas:
            if not self.database.exist(meta.title):
                count = count + self._check_update_for_meta(meta)

            if count == DB_UPDATE_COUNT:
                break

        return count

    def _check_update_for_meta(self, meta):
        if not self.database.exist(meta.title):
            logger.info("Fetch %s", meta.title)
            parser = get_parser_for_site(meta.url)
            content = parser.get_post_content(meta.url)
            self.database.insert_new_post(content)
            return 1
        return 0
