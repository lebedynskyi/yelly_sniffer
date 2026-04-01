import logging
from pathlib import Path

from typing import Dict, Optional

from src.client import get_client
from src.parser import Parser, ParserMetaResult, ParseArticleResult

logger = logging.getLogger(__name__)


class Crawler:
    configs: Dict = None

    def __init__(self, workdir: Path, configs: Dict):
        self.configs = configs
        self.workdir = workdir

    def crawl_meta(self, site: str) -> list[ParserMetaResult]:
        logger.info(f"🐢Crawling meta for {site}")

        browser = get_client(self.workdir)
        try:
            response = browser.load_page(site)
        except BaseException as e:
            browser.screen_shot(self.workdir, "meta_error.png")
            raise e

        # response = None
        # with open(os.path.join(self.workdir, "dzen_group_page.html")) as f:
        #     response = f.read()

        parser = Parser.get_parser(site)
        return parser.parse_metas(response)

    def crawl_article(self, meta: ParserMetaResult) -> Optional[ParseArticleResult]:
        logger.info(f"🐢Crawling article for {meta.url}")
        browser = get_client(self.workdir)

        try:
            response = browser.load_page(meta.url)
        except BaseException as e:
            browser.screen_shot(self.workdir, "article_error.png")
            raise e

        # response = None
        # with open(os.path.join(self.workdir, "dzen_article_page.html")) as f:
        #     response = f.read()

        parser = Parser.get_parser(meta.url)
        return parser.parse_article(response)
