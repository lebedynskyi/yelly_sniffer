from typing import Optional

from bs4 import BeautifulSoup


def extract_canonical_url(soup: BeautifulSoup) -> Optional[str]:
    og_url = soup.find("meta", property="og:url")
    if og_url and og_url.get("content"):
        return og_url["content"]

    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        return canonical["href"]

    return None
