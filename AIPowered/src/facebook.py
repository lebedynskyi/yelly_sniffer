import logging
import random
import time
from pathlib import Path

from src.client import get_client
from src.data import DBArticle

logger = logging.getLogger(__name__)

XPATH_COOKIES = [
    "//div[@role='button' and @aria-label='Разрешить все cookie']",
    "//div[@role='button' and @aria-label='Allow all cookies']"
]

XPATH_CREATE_ACCOUNTS = [
    "//div[@role='button' and @aria-label='Создать новый аккаунт']",
    "//div[@role='button' and @aria-label='Create new account']"
]

XPATH_USER_NAME = '//input[@type="text" and @name="email"]'
XPATH_PASSWORD = '//input[@type="password" and @name="pass"]'
XPATH_LOGINS = [
    "//div[@aria-label='Войти на Facebook']",
    "//div[@aria-label='Log in to Facebook']"
]
XPATH_SWITCHS = [
    "//span[.='Переключиться']"
]


class FBAuto:
    def __init__(self, workdir: Path, config: dict[str, str]):
        self.workdir = workdir
        self.config = config
        self.client = get_client(workdir, headless=False)

    def publish_post(self, article: DBArticle) -> bool:
        logger.info(f"Publishing post {article.meta_title}")
        self.auth()

        return False

    def auth(self):
        fb_page = self.config["fb_page"]
        logger.info(f"Open and auth into {fb_page}")
        self.client.load_page(fb_page)
        accept_cookie = self.client.xpath_element(*XPATH_COOKIES, nth=1)
        if accept_cookie:
            logger.info("Not logged. See cookie")

            accept_cookie.click()
            logger.info("Cookie accepted")

        create_account = self.client.xpath_element(*XPATH_CREATE_ACCOUNTS)
        if create_account:
            logger.info("Not logged. Logging in!")
            username = self.client.xpath_element(XPATH_USER_NAME)
            username.click()
            self.client.page.keyboard.type(self.config["fb_user"])
            time.sleep(1)

            # password = self.client.xpath_element(XPATH_PASSWORD)
            # password.click()
            self.client.page.keyboard.press("Tab")
            self.client.page.keyboard.type(self.config["fb_password"])

            log_in = self.client.xpath_element(*XPATH_LOGINS)
            log_in.click()
            time.sleep(10)

        switch = self.client.xpath_element(*XPATH_SWITCHS, nth=3)
        if switch:
            logger.debug("Switch to page")
            time.sleep(5)

        logger.info("Auth finished")
        self.client.save_state()