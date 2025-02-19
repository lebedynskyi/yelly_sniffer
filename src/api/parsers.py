import logging
import re
import time
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from src import io
from src.models import PostContent, PostMeta

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


class Parser(ABC):
    @abstractmethod
    def get_posts_meta(self, site_url):
        pass

    @abstractmethod
    def get_post_content(self, post_url):
        pass


class YellyParser(Parser):
    def get_posts_meta(self, site_url):
        page = io.do_get(site_url)
        parser = BeautifulSoup(page, 'html.parser')

        posts = parser.find_all("article")
        if not posts:
            posts = parser.find_all("span", itemprop="headline")
            post_urls = [PostMeta(p.find("a").get_text(strip=True), p.find("a").get("href")) for p in posts]
        else:
            post_urls = [PostMeta(p.find("span", itemprop="headline").get_text(strip=True), p.find("a").get("href")) for
                         p in posts]
        return post_urls

    def get_post_content(self, post_url):
        post = io.do_get(post_url)
        parser = BeautifulSoup(post, 'html.parser')

        post_title = parser.find("h1", {"class": "entry-title"}).get_text(strip=True)
        content = parser.find("div", {"class": "entry-content"})

        # Add some clean ip of content
        for ins in content.find_all("ins", {'class': 'adsbygoogle'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'b-r--before_content'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'b-r--after_content'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'nodesktop'}):
            ins.decompose()

        for ins in content.find_all("div", {"id": re.compile("^yandex")}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'ads'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'nomobile'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'r-bl'}):
            ins.decompose()

        for ins in content.find_all("script"):
            ins.decompose()

        for ins in content.find_all("center"):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'panel'}):
            ins.name = "p"

        feature_image = None
        for img in content.find_all("img"):
            feature_image = img["src"]
            img["alt"] = post_title
            try:
                img["class"].append("aligncenter")
                img["class"].append("size-full")
            except:
                img["class"] = "aligncenter size-full"

            img["sizes"] = None
            img["srcset"] = None

        return PostContent(post_title, content.renderContents(prettyPrint=True).decode("utf8"), post_url, feature_image)


class CrykamiParser(Parser):
    def get_posts_meta(self, site_url):
        page = io.do_get(site_url)
        parser = BeautifulSoup(page, 'html.parser')

        posts = parser.find_all("article")
        if not posts:
            return []

        post_urls = [PostMeta(p.find("h2").get_text(strip=True), p.find("a").get("href")) for p in posts]
        return post_urls

    def get_post_content(self, post_url):
        post = io.do_get(post_url)
        parser = BeautifulSoup(post, 'html.parser')

        post_title = parser.find("h1", {"class": "entry-title"}).get_text(strip=True)
        content = parser.find("div", {"class": "entry-content"})

        # Add some clean ip of content
        for ins in content.find_all("ins", {'class': 'adsbygoogle'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'b-r--before_content'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'b-r--after_content'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'nodesktop'}):
            ins.decompose()

        for ins in content.find_all("div", {"id": re.compile("^yandex")}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'ads'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'nomobile'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'r-bl'}):
            ins.decompose()

        for ins in content.find_all("script"):
            ins.decompose()

        for ins in content.find_all("style"):
            ins.decompose()

        for ins in content.find_all("center"):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'panel'}):
            ins.name = "p"

        feature_image = None
        for img in content.find_all("img"):
            feature_image = img["src"]
            img["alt"] = post_title
            try:
                img["class"].append("aligncenter")
                img["class"].append("size-full")
            except:
                img["class"] = "aligncenter size-full"

            img["sizes"] = None
            img["srcset"] = None
        return PostContent(post_title, content.renderContents(prettyPrint=True).decode("utf8"), post_url, feature_image)


class UkrainnParser(Parser):
    def get_posts_meta(self, site_url):
        page = io.do_get(site_url)
        parser = BeautifulSoup(page, 'html.parser')

        posts = parser.find_all("header", {'class': 'entry-header'})
        post_urls = [PostMeta(p.find("h3").get_text(strip=True), p.find("a").get("href")) for p in posts]
        return post_urls

    def get_post_content(self, post_url):
        post = io.do_get(post_url)
        parser = BeautifulSoup(post, 'html.parser')

        post_title = parser.find("h3", {"class": "single-title"}).get_text(strip=True)
        content = parser.find("div", {"class": "entry-content"})

        # Add some clean ip of content
        for ins in content.find_all("ins", {'class': 'adsbygoogle'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'b-r--before_content'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'b-r--after_content'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'nodesktop'}):
            ins.decompose()

        for ins in content.find_all("div", {"id": re.compile("^yandex")}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'ads'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'nomobile'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'r-bl'}):
            ins.decompose()

        for ins in content.find_all("script"):
            ins.decompose()

        for ins in content.find_all("style"):
            ins.decompose()

        for ins in content.find_all("center"):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'panel'}):
            ins.name = "p"

        feature_image = None
        for img in content.find_all("img"):
            feature_image = img["src"]
            img["alt"] = post_title
            try:
                img["class"].append("aligncenter")
                img["class"].append("size-full")
            except:
                img["class"] = "aligncenter size-full"

            img["sizes"] = None
            img["srcset"] = None

        return PostContent(post_title, content.renderContents(prettyPrint=True).decode("utf8"), post_url, feature_image)


class HappyTimesParser(Parser):
    def get_posts_meta(self, site_url):
        page = io.do_get(site_url)
        parser = BeautifulSoup(page, 'html.parser')

        posts = parser.find_all("article")
        if not posts:
            return []

        post_urls = [PostMeta(p.find("h2").get_text(strip=True), p.find("a").get("href")) for p in posts]
        return post_urls

    def get_post_content(self, post_url):
        post = io.do_get(post_url)
        parser = BeautifulSoup(post, 'html.parser')

        post_title = parser.find("div", {"class": "the_title"}).get_text(strip=True)
        content = parser.find("div", {"class": "the_content"})

        # Add some clean ip of content
        for ins in content.find_all("ins", {'class': 'adsbygoogle'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'b-r--before_content'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'b-r--after_content'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'nodesktop'}):
            ins.decompose()

        for ins in content.find_all("div", {"id": re.compile("^yandex")}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'ads'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'afw'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'nomobile'}):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'r-bl'}):
            ins.decompose()

        for ins in content.find_all("script"):
            ins.decompose()

        for ins in content.find_all("style"):
            ins.decompose()

        for ins in content.find_all("center"):
            ins.decompose()

        for ins in content.find_all("div", {'class': 'panel'}):
            ins.name = "p"

        feature_image = None
        for img in content.find_all("img"):
            feature_image = img["src"]
            img["alt"] = post_title
            try:
                img["class"].append("aligncenter")
                img["class"].append("size-full")
            except:
                img["class"] = "aligncenter size-full"

            img["sizes"] = None
            img["srcset"] = None
        return PostContent(post_title, content.renderContents(prettyPrint=True).decode("utf8"), post_url,
                           feature_image)


class DzenRuParser(Parser):
    _driver = None

    def __init__(self, headless=True):
        self.headless = headless

    def get_posts_meta(self, site_url):
        self._init_driver()
        self._driver.maximize_window()
        self._driver.get(site_url)
        time.sleep(5)
        posts = self._driver.find_elements(By.CLASS_NAME, "desktop2--card-article__cardWrapper-1S")
        posts_meta = []
        for p in posts:
            a_href = p.find_elements(By.TAG_NAME, "a")[1]
            posts_meta.append(PostMeta(a_href.text, a_href.get_attribute("href")))
        return posts_meta

    def get_post_content(self, post_url):
        self._init_driver()
        self._driver.get(post_url)
        time.sleep(5)
        post = self._driver.find_element(By.CLASS_NAME, "content--article-item-content__content-1S")
        post_title = post.find_element(By.TAG_NAME, "h1").text

        content = post.find_element(By.CLASS_NAME, "content--article-render__container-1k")
        post_content = content.get_attribute("innerHTML")
        parser = BeautifulSoup(post_content, 'html.parser')
        feature_image = None
        for img in parser.find_all("img"):
            feature_image = img["src"]
            img["alt"] = post_title
            try:
                img["class"].append("aligncenter")
                img["class"].append("size-full")
            except:
                img["class"] = "aligncenter size-full"

            img["sizes"] = None
            img["srcset"] = None

        return PostContent(post_title, post_content, post_url, feature_image)

    def _init_driver(self):
        if not self._driver:
            self._driver = self._chrome_driver()

    def _chrome_driver(self):
        from selenium.webdriver.chrome.options import Options
        prefs = {"profile.default_content_setting_values.notifications": 2}
        opts = Options()
        opts.add_experimental_option("prefs", prefs)
        # opts.add_argument('--user-data-dir=profiles/chrome')
        opts.add_argument('--profile-directory=Default')
        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        if self.headless:
            opts.add_argument('--start-minimized')
            opts.add_argument('--headless')
            opts.add_argument('--disable-gpu')
        return webdriver.Chrome(options=opts)


if __name__ == "__main__":
    pars = HappyTimesParser()
    meta = pars.get_posts_meta("https://happytimes.info/")
    print(meta)

    p = pars.get_post_content(meta[0].url)
    print(p)
