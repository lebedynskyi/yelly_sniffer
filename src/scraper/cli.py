import argparse
import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from scraper.fetching import get_fetcher
from scraper.fixing import get_fixer
from scraper.parsing import get_parser
from scraper.pipeline import SiteHandlers, run_pipeline
from scraper.post_tracking import ArticleStore
from scraper.publishing.facebook import GraphApiPublisher
from scraper.publishing.wordpress import WordpressRpcPublisher
from scraper.sanitizer import Bs4HtmlSanitizer
from scraper.settings import AISettings

logger = logging.getLogger(__name__)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scraper")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--scrape", action="store_true", default=False, help="Enable scraping new articles")
    parser.add_argument("--xmlrpc", action="store_true", default=False, help="Enable WordPress publishing")
    parser.add_argument("--facebook", action="store_true", default=False, help="Enable Facebook publishing")
    return parser


def load_config(config_path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

    args = build_arg_parser().parse_args()
    config = load_config(args.config)

    store = ArticleStore(Path(config["database"]["path"]))
    sanitizer = Bs4HtmlSanitizer()

    sites = []
    fixer = None
    if args.scrape:
        fixer = get_fixer(AISettings())
        sites = [
            SiteHandlers(
                name=site["name"],
                url=site["url"],
                fetcher=get_fetcher(site),
                parser=get_parser(site["name"]),
            )
            for site in config["sites"]
        ]

    wp_publisher = None
    if args.xmlrpc:
        wp_publisher = WordpressRpcPublisher(
            rpc_url=os.environ["WP_RPC_URL"],
            rpc_user=os.environ["WP_RPC_USER"],
            rpc_password=os.environ["WP_RPC_PASSWORD"],
        )

    fb_publisher = None
    if args.facebook:
        fb_publisher = GraphApiPublisher(
            page_id=os.environ["FB_PAGE_ID"],
            access_token=os.environ["FB_PAGE_ACCESS_TOKEN"],
        )

    run_pipeline(
        sites=sites,
        store=store,
        sanitizer=sanitizer,
        fixer=fixer,
        wp_publisher=wp_publisher,
        fb_publisher=fb_publisher,
        do_scrape=args.scrape,
        do_xmlrpc=args.xmlrpc,
        do_facebook=args.facebook,
    )


if __name__ == "__main__":
    main()
