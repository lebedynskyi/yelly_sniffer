import logging
import re

from bs4 import BeautifulSoup

from src import io
from src.models import PostMeta, PostContent

PAGES_PATTERN = "{site}/page/{page}"

logger = logging.getLogger(__name__)


class YellyApi:
    def __init__(self):
        pass

    @staticmethod
    def get_post_content(link):
        post = io.do_get(link)
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

        return PostContent(post_title, content.renderContents(prettyPrint=True).decode("utf8"), link, feature_image)

    @staticmethod
    def get_posts_meta(page_url):
        logger.debug("Getting metas from page %s", page_url)

        page = io.do_get(page_url)
        parser = BeautifulSoup(page, 'html.parser')

        posts = parser.find_all("article")
        if not posts:
            posts = parser.find_all("span", itemprop="headline")
            post_urls = [PostMeta(p.find("a").get_text(strip=True), p.find("a").get("href")) for p in posts]
        else:
            post_urls = [PostMeta(p.find("span", itemprop="headline").get_text(strip=True), p.find("a").get("href")) for
                         p in
                         posts]
        return post_urls

    @staticmethod
    def get_page_links(site, start, end):
        if site.endswith('/'):
            site = site[:-1]
        return [PAGES_PATTERN.format(site=site, page=p + 1) for p in range(start, end)]

    @staticmethod
    def get_page_link(site, index):
        if site.endswith('/'):
            site = site[:-1]
        return PAGES_PATTERN.format(site=site, page=index)
