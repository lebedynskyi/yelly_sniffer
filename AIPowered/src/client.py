import logging
import os.path
from os import PathLike
from pathlib import Path
from typing import Optional

import playwright.sync_api
import requests
from playwright.sync_api import sync_playwright, ViewportSize, Locator

STATE_FILE_NAME = "state.json"

logger = logging.getLogger(__name__)


class BrowserClient:
    def __init__(self, workdir: Path, headless: bool = True, timeout_ms: int = 10_000):
        self.workdir = workdir
        self.state_file = os.path.abspath(os.path.join(workdir, STATE_FILE_NAME))
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        self.context = self.browser.new_context(
            viewport=ViewportSize(width=1024, height=768),
            storage_state=self.state_file,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            ),
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(timeout_ms)

    def screen_shot(self, directory: PathLike, name: str):
        self.page.screenshot(path=os.path.join(directory, name), full_page=True)

    def load_page(self, url: str, retries=3) -> str:
        for i in range(1, retries):
            try:
                self.page.goto(url, wait_until="domcontentloaded")
                content =  self.page.content()
                self.save_state()
                return content
            except:
                logger.info(f"Failed to load html for {url}. Retry {i}")
        raise IOError(f"Unable to fetch html {url} after {retries} attempts")

    def save_state(self):
        self.context.storage_state(path=self.state_file)

    def xpath_element(self, *args, nth=0, timeout=1500) -> Optional[Locator]:
        logger.info(f"Looking for xpath elements {args}")

        for xpath in args:
            locator = self.page.locator(f"xpath={xpath}").nth(nth)
            try:
                locator.wait_for(state="visible", timeout=timeout)
                return locator
            except playwright.sync_api.TimeoutError:
                continue

        return None

    def close(self):
        self.context.close()
        self.browser.close()
        self.playwright.stop()


class HttpClient:
    def __init__(
            self,
            timeout: int = 15,
            user_agent: str = "Mozilla/5.0 (Apple MackBook pro/1.0)"
    ):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml",
        })
        self.timeout = timeout

    def get(self, url: str) -> requests.Response:
        response = self.session.get(
            url,
            timeout=self.timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        return response

    def close(self):
        self.session.close()


_cached_client: Optional[BrowserClient] = None


def get_client(workdir: Path, headless=True) -> BrowserClient:
    global _cached_client
    if _cached_client is None:
        _cached_client = BrowserClient(workdir, headless=headless)
    return _cached_client
