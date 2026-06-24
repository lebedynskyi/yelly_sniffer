import dataclasses
import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PUBLISH_TARGETS = ("wordpress", "facebook")

_CREATE_ARTICLES = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meta_title TEXT NOT NULL,
    article_title TEXT NOT NULL,
    article_body TEXT NOT NULL,
    original_url TEXT NOT NULL UNIQUE,
    discovered_at TEXT NOT NULL,
    wordpress_published INTEGER NOT NULL DEFAULT 0,
    facebook_published INTEGER NOT NULL DEFAULT 0,
    wordpress_url TEXT,
    feature_image_url TEXT
)
"""

_ADD_COLUMN_IF_MISSING = [
    ("wordpress_url", "ALTER TABLE articles ADD COLUMN wordpress_url TEXT"),
    ("feature_image_url", "ALTER TABLE articles ADD COLUMN feature_image_url TEXT"),
]

_TARGET_COLUMNS = {
    "wordpress": "wordpress_published",
    "facebook": "facebook_published",
}


@dataclasses.dataclass
class Article:
    meta_title: str
    article_title: str
    article_body: str
    original_url: str
    discovered_at: str
    wordpress_published: bool = False
    facebook_published: bool = False
    wordpress_url: Optional[str] = None
    feature_image_url: Optional[str] = None
    id: Optional[int] = None


def _row_to_article(row: sqlite3.Row) -> Article:
    return Article(
        id=row["id"],
        meta_title=row["meta_title"],
        article_title=row["article_title"],
        article_body=row["article_body"],
        original_url=row["original_url"],
        discovered_at=row["discovered_at"],
        wordpress_published=bool(row["wordpress_published"]),
        facebook_published=bool(row["facebook_published"]),
        wordpress_url=row["wordpress_url"],
        feature_image_url=row["feature_image_url"],
    )


class ArticleStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(_CREATE_ARTICLES)
        self._migrate_missing_columns()
        self.connection.commit()

    def _migrate_missing_columns(self) -> None:
        existing = {row["name"] for row in self.connection.execute("PRAGMA table_info(articles)")}
        for column, ddl in _ADD_COLUMN_IF_MISSING:
            if column not in existing:
                self.connection.execute(ddl)

    def exists(self, meta_title: str, original_url: str) -> bool:
        cursor = self.connection.execute(
            "SELECT 1 FROM articles WHERE meta_title = ? OR original_url = ?",
            (meta_title, original_url),
        )
        return cursor.fetchone() is not None

    def save(self, article: Article) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO articles (
                meta_title, article_title, article_body, original_url,
                discovered_at, wordpress_published, facebook_published,
                wordpress_url, feature_image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                article.meta_title,
                article.article_title,
                article.article_body,
                article.original_url,
                article.discovered_at,
                int(article.wordpress_published),
                int(article.facebook_published),
                article.wordpress_url,
                article.feature_image_url,
            ),
        )
        self.connection.commit()
        return cursor.lastrowid

    def find_unpublished(self, target: str) -> list[Article]:
        column = self._target_column(target)
        condition = f"{column} = 0"
        if target == "facebook":
            condition += " AND wordpress_url IS NOT NULL AND feature_image_url IS NOT NULL"
        cursor = self.connection.execute(
            f"SELECT * FROM articles WHERE {condition} ORDER BY id DESC"
        )
        return [_row_to_article(row) for row in cursor.fetchall()]

    def mark_published(self, article_id: int, target: str) -> None:
        column = self._target_column(target)
        self.connection.execute(
            f"UPDATE articles SET {column} = 1 WHERE id = ?", (article_id,)
        )
        self.connection.commit()

    def set_wordpress_url(self, article_id: int, url: str) -> None:
        self.connection.execute(
            "UPDATE articles SET wordpress_url = ? WHERE id = ?", (url, article_id)
        )
        self.connection.commit()

    @staticmethod
    def _target_column(target: str) -> str:
        try:
            return _TARGET_COLUMNS[target]
        except KeyError:
            raise ValueError(
                f"Unknown publish target '{target}', expected one of {PUBLISH_TARGETS}"
            ) from None
