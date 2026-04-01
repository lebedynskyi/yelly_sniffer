import dataclasses
from abc import ABC, abstractmethod
from os import PathLike
from typing import Union, Optional
from bs4 import BeautifulSoup

from src.core.utils import extract_host, sanitize_whitespaces, sanitize_url_remove_query


@dataclasses.dataclass
class ParserMetaResult:
    title: str
    url: str


@dataclasses.dataclass
class ParseArticleResult:
    title: str
    body: str


class Parser(ABC):
    host: str

    def __init__(self, host: str):
        self.host = host

    @staticmethod
    def get_parser(uri: Union[str, PathLike]) -> "Parser":
        host = extract_host(uri)
        return parsers[host]

    @abstractmethod
    def parse_metas(self, html) -> list[ParserMetaResult]:
        pass

    @abstractmethod
    def parse_article(self, html) -> ParseArticleResult:
        pass


class DzenParser(Parser):
    def __init__(self, host: str):
        super().__init__(host)

    def parse_metas(self, html) -> Optional[list[ParserMetaResult]]:
        soup = BeautifulSoup(html, "html.parser")
        articles = soup.select('article[data-card-type="card-article"]')
        result = []
        for a in articles:
            a_href = a.find_all("a")
            title_divs = a.select('div[data-testid="card-part-title"]')
            if a_href and title_divs:
                link_raw = a_href[0]["href"]
                link = link_raw
                title_raw = title_divs[0].get_text(separator="\n", strip=True)
                title = sanitize_whitespaces(title_raw)
                result.append(ParserMetaResult(title, link))

        if result:
            return result

        return None

    def parse_article(self, html) -> Optional[ParseArticleResult]:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("h1").get_text(strip=True)
        body = soup.select('div[itemprop="articleBody"]')
        if title and body:
            body_content = body[0].decode_contents()
            return ParseArticleResult(title, body_content)

        return None


parsers = {
    "dzen.ru": DzenParser("dzen.ru")
}
