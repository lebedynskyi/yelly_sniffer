import re
from os import PathLike
from typing import Union
from urllib.parse import urlparse, urlunparse


def normalize_url(raw: str) -> str:
    if not raw:
        raise ValueError("Empty URL")

    raw = raw.strip()

    # Add scheme if missing
    if "://" not in raw:
        raw = "https://" + raw

    parsed = urlparse(raw)

    if not parsed.netloc:
        raise ValueError(f"Invalid URL: {raw}")

    # Remove trailing slash from path (but keep root)
    path = parsed.path.rstrip("/")
    if path == "":
        path = ""

    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        path=path
    )

    return urlunparse(normalized)


def extract_host(url: Union[str, PathLike]) -> str:
    parsed = urlparse(url)
    return parsed.netloc


def sanitize_whitespaces(text: str) -> str:
    if not text:
        return ""

    # Strip leading/trailing whitespace
    text = text.strip()

    # Replace any whitespace sequence with a single space
    text = re.sub(r"\s+", " ", text)

    return text


def sanitize_url_remove_query(url: str) -> str:
    parsed = urlparse(url)
    sanitized = parsed._replace(query="", fragment="", )
    return urlunparse(sanitized)
