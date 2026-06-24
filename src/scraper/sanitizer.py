import logging
import re

import bleach
from bs4 import BeautifulSoup, NavigableString

logger = logging.getLogger(__name__)

CTA_PATTERNS = [
    r"став(ь|ьте)\s+лайк",
    r"подписывай(ся|тесь)",
    r"подписка\s+на\s+канал",
    r"пиши(те)?\s+комментар",
    r"оставляй(те)?\s+комментар",
    r"читай(те)?\s+другие",
    r"мой\s+канал",
    r"смотрите\s+также",
]

ALLOWED_PROTOCOLS = ["http", "https"]

ALLOWED_TAGS = [
    "p", "br",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "b",
    "em", "i",
    "ul", "ol", "li",
    "blockquote",
    "a",
    "img",
    "code", "pre",
]

ALLOWED_TAG_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
}

BLOCK_TAGS = {
    "p", "div", "section", "article",
    "blockquote",
    "ul", "ol", "li",
}


class Bs4HtmlSanitizer:
    def sanitize_html(self, html: str) -> str:
        logger.info("Sanitizing article HTML")
        clean = self.clean_html(html)

        soup = BeautifulSoup(clean, "html.parser")
        for text_node in soup.find_all(string=True):
            if not isinstance(text_node, NavigableString):
                continue

            text = text_node.strip()
            if not text:
                continue

            if self.is_cta_line(text):
                text_node.extract()

        changed = True
        while changed:
            changed = False
            for tag in soup.find_all(BLOCK_TAGS):
                if tag.find(["img", "iframe", "video"]):
                    continue

                if not tag.get_text(strip=True):
                    tag.decompose()
                    changed = True

        return self.clean_html(str(soup))

    def clean_html(self, html: str) -> str:
        return bleach.clean(
            html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_TAG_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,
            strip_comments=True,
        )

    def sanitize_text(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        cleaned = [line for line in lines if line and not self.is_cta_line(line)]
        return "\n".join(cleaned)

    def is_cta_line(self, line: str) -> bool:
        text = line.lower()

        for pattern in CTA_PATTERNS:
            if re.search(pattern, text):
                return True

        if line.isupper() and len(line) > 20:
            return True

        return False
