from bs4 import BeautifulSoup

from scraper.parsing import Article, ArticleMeta, Parser
from scraper.parsing.canonical import extract_canonical_url
from scraper.parsing.cleanup import strip_by_selectors

# storyx.ru has no prior parser to port; selectors assume a standard WordPress
# entry-title/entry-content theme like the other sites, pending verification
# against the live site.
STRIP_SELECTORS = [
    "ins.adsbygoogle",
    "div.ads",
    'div[id^="yandex"]',
    "script",
    "style",
]


class StoryxParser(Parser):
    def parse_metas(self, html: str) -> list[ArticleMeta]:
        soup = BeautifulSoup(html, "html.parser")

        articles = soup.find_all("article")
        return [
            ArticleMeta(title=a.find("h2").get_text(strip=True), url=a.find("a")["href"])
            for a in articles
        ]

    def parse_article(self, html: str) -> Article:
        soup = BeautifulSoup(html, "html.parser")

        title = soup.find("h1", class_="entry-title").get_text(strip=True)
        content = soup.find("div", class_="entry-content")
        strip_by_selectors(content, STRIP_SELECTORS)

        feature_image = None
        img = content.find("img")
        if img:
            feature_image = img.get("src")

        url = extract_canonical_url(soup)
        return Article(title=title, body=str(content), url=url, feature_image=feature_image)
