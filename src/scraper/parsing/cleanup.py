from bs4 import BeautifulSoup, Tag


def strip_by_selectors(soup: BeautifulSoup | Tag, selectors: list[str]) -> None:
    for selector in selectors:
        for element in soup.select(selector):
            element.decompose()
