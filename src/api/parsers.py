import logging
import re
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from src import io
from src.models import PostContent, PostMeta

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


if __name__ == "__main__":
    pars = CrykamiParser()
    meta = pars.get_posts_meta("https://cpykami.ru/")
    print(meta)

    p = pars.get_post_content(meta[0].url)
    print(p)
