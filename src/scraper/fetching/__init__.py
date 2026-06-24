import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class FetchError(Exception):
    pass


class Fetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> str:
        raise NotImplementedError


class RequestsFetcher(Fetcher):
    def __init__(self, user_agent: str = DEFAULT_USER_AGENT, cookies: Optional[dict] = None):
        self.user_agent = user_agent
        self.cookies = cookies or {}

    def fetch(self, url: str) -> str:
        logger.info("Fetching %s via requests", url)
        response = requests.get(url, headers={"User-Agent": self.user_agent}, cookies=self.cookies)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise FetchError(f"Failed to fetch {url}: {e}") from e
        return response.text


class PlaywrightFetcher(Fetcher):
    def __init__(self, headless: bool = True):
        self.headless = headless

    def fetch(self, url: str) -> str:
        logger.info("Fetching %s via playwright", url)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            try:
                page = browser.new_page()
                page.goto(url)
                return page.content()
            finally:
                browser.close()


_FETCHER_TYPES = {
    "requests": RequestsFetcher,
    "playwright": PlaywrightFetcher,
}


def get_fetcher(site_config: dict) -> Fetcher:
    choice = site_config.get("fetcher", "requests")
    try:
        fetcher_cls = _FETCHER_TYPES[choice]
    except KeyError:
        raise ValueError(
            f"Unknown fetcher '{choice}', expected one of {list(_FETCHER_TYPES)}"
        ) from None
    return fetcher_cls()
