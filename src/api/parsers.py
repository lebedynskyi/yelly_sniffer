import logging
import re
import time
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from src import io
from src.api.web_driver import uc_chrome_driver, chrome_driver
from src.models import PostContent, PostMeta

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

    def get_posts_meta(self, site_url):
        self.init_driver()
        self._driver.maximize_window()
        self._driver.get(site_url)
        time.sleep(3)
        posts = self._driver.find_elements(By.TAG_NAME, "article")
        posts_meta = []
        for p in posts:
            a_href = p.find_elements(By.TAG_NAME, "a")[0]
            posts_meta.append(PostMeta(a_href.text, a_href.get_attribute("href")))
        return posts_meta

    def get_post_content(self, post_url):
        self.init_driver()
        self._driver.get(post_url)
        time.sleep(3)
        post = self._driver.find_element(By.CLASS_NAME, "content--article-item-content__content-1S")
        post_title = post.find_element(By.TAG_NAME, "h1").text

        content = post.find_element(By.CLASS_NAME, "content--article-render__container-1k")
        post_content = content.get_attribute("innerHTML")
        content_parser = BeautifulSoup(post_content, 'html.parser')
        feature_image = None
        for img in content_parser.find_all("img"):
            feature_image = img["src"]
            img["alt"] = post_title
            try:
                img["class"].append("aligncenter")
                img["class"].append("size-full")
            except:
                img["class"] = "aligncenter size-full"

            img["sizes"] = None
            img["srcset"] = None

            while img.parent and (img.parent.has_attr("class") or img.parent.name != "div"):
                img.parent.unwrap()

            for div in img.parent.find_all("div"):
                div.decompose()

        links = content_parser.findAll("a", {'class': 'content--article-link__articleLink-OU'})
        for l in links:
            l.decompose()

        for item in content_parser.findAll("div", {'data-ahgkhv4yl': 'embed-block_yandex-zen-publication'}):
            item.decompose()

        source_link = content_parser.new_tag(name="a", href=post_url)
        source_link.string = "Источник"
        content_parser.append(content_parser.new_tag("p"))
        content_parser.append(source_link)
        post_content = content_parser.renderContents(prettyPrint=True).decode("utf8")
        return PostContent(
            post_title, post_content, post_url, feature_image
        )

    def init_driver(self):
        if not self._driver:
            self._driver = chrome_driver()


if __name__ == "__main__":
    pars = HappyTimesParser()
    meta = pars.get_posts_meta("https://happytimes.info/")
    print(meta)

    p = pars.get_post_content(meta[0].url)
    print(p)
