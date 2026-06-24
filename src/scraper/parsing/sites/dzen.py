from bs4 import BeautifulSoup

from scraper.parsing import Article, ArticleMeta, Parser
from scraper.parsing.canonical import extract_canonical_url
from scraper.parsing.cleanup import strip_by_selectors

STRIP_SELECTORS = [
    "a.content--article-link__articleLink-OU",
    'div[data-ahgkhv4yl="embed-block_yandex-zen-publication"]',
]


class DzenParser(Parser):
    def parse_metas(self, html: str) -> list[ArticleMeta]:
        soup = BeautifulSoup(html, "html.parser")

        cards = soup.select('article[data-card-type="card-article"]')
        metas = []
        for card in cards:
            link = card.find("a")
            title_div = card.select_one('[data-testid="card-part-title"]')
            title = title_div.get_text(strip=True) if title_div else card.get_text(strip=True)
            metas.append(ArticleMeta(title=title, url=link["href"]))
        return metas

    def parse_article(self, html: str) -> Article:
        soup = BeautifulSoup(html, "html.parser")

        container = soup.select_one('[class^="content--article-item-content_"]')
        title = container.find("h1").get_text(strip=True)
        content = container.find("div", class_="content--article-render__container-1k")
        strip_by_selectors(content, STRIP_SELECTORS)

        feature_image = None
        img = content.find("img")
        if img:
            feature_image = img.get("src")

        url = extract_canonical_url(soup)
        return Article(title=title, body=str(content), url=url, feature_image=feature_image)
