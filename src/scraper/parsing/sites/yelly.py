from bs4 import BeautifulSoup

from scraper.parsing import Article, ArticleMeta, Parser
from scraper.parsing.canonical import extract_canonical_url
from scraper.parsing.cleanup import strip_by_selectors

STRIP_SELECTORS = [
    "ins.adsbygoogle",
    "div.b-r--before_content",
    "div.b-r--after_content",
    "div.nodesktop",
    'div[id^="yandex"]',
    "div.ads",
    "div.nomobile",
    "div.r-bl",
    "script",
    "center",
]


class YellyParser(Parser):
    def parse_metas(self, html: str) -> list[ArticleMeta]:
        soup = BeautifulSoup(html, "html.parser")

        articles = soup.find_all("article")
        if articles:
            return [
                ArticleMeta(
                    title=a.find("span", itemprop="headline").get_text(strip=True),
                    url=a.find("a")["href"],
                )
                for a in articles
            ]

        headlines = soup.find_all("span", itemprop="headline")
        return [
            ArticleMeta(title=h.find("a").get_text(strip=True), url=h.find("a")["href"])
            for h in headlines
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
