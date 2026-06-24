import dataclasses
from abc import ABC, abstractmethod
from typing import Optional


@dataclasses.dataclass
class ArticleMeta:
    title: str
    url: str


@dataclasses.dataclass
class Article:
    title: str
    body: str
    url: str
    feature_image: Optional[str] = None


class Parser(ABC):
    @abstractmethod
    def parse_metas(self, html: str) -> list[ArticleMeta]:
        raise NotImplementedError

    @abstractmethod
    def parse_article(self, html: str) -> Article:
        raise NotImplementedError


def get_parser(site_name: str) -> Parser:
    from scraper.parsing.sites.crykami import CrykamiParser
    from scraper.parsing.sites.dzen import DzenParser
    from scraper.parsing.sites.happytimes import HappyTimesParser
    from scraper.parsing.sites.storyx import StoryxParser
    from scraper.parsing.sites.yelly import YellyParser

    registry = {
        "yelly": YellyParser,
        "crykami": CrykamiParser,
        "happytimes": HappyTimesParser,
        "dzen": DzenParser,
        "storyx": StoryxParser,
    }
    try:
        parser_cls = registry[site_name]
    except KeyError:
        raise ValueError(f"Unknown site '{site_name}', expected one of {list(registry)}") from None
    return parser_cls()
