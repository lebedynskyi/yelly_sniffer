import dataclasses
import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

CREATE_ARTICLES = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meta_title TEXT NOT NULL,
    article_title TEXT NOT NULL,
    article_body TEXT NOT NULL,
    original_url TEXT NOT NULL UNIQUE,
    time TEXT NOT NULL,
    rpc INTEGER NOT NULL DEFAULT 0,
    fb INTEGER NOT NULL DEFAULT 0
)
"""


@dataclasses.dataclass
class DBArticle:
    meta_title: str
    article_title: str
    article_body: str
    original_url: str
    time: str
    rpc: bool = False
    fb: bool = False
    id: int = 0


class SQLiteDatabase:
    connection = None

    def __init__(self, wd, db_name="database.sqlite"):
        self.wd = wd
        self.db_file = os.path.join(wd, db_name)
        if not os.path.exists(self.db_file):
            logger.info(f"⛁ Database '{self.db_file}' not exist. Create it")
            self._create_database()
        else:
            logger.info(f"⛁ Database '{self.db_file}' exist. Use it")
            self._connect_to_db()

    def exist_meta(self, title) -> bool:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM articles where meta_title=?", (title,))
        return cursor.fetchone() is not None

    def save_article(self, article: DBArticle):
        query = """
            INSERT OR IGNORE INTO articles (
                meta_title,
                article_title,
                article_body,
                original_url,
                time,
                rpc,
                fb
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """

        self.connection.execute(
            query,
            (
                article.meta_title,
                article.article_title,
                article.article_body,
                article.original_url,
                article.time,
                int(article.rpc),
                int(article.fb),
            )
        )
        self.connection.commit()

    def find_by_rpc_status(self, status) -> list[DBArticle]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM articles where rpc=? ORDER BY id DESC", (status,))
        res = cursor.fetchall()
        return [DBArticle(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[0]) for r in res]

    def find_by_fb_status(self, status) -> list[DBArticle]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM articles where fb=? ORDER BY id DESC", (status,))
        res = cursor.fetchall()
        return [DBArticle(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[0]) for r in res]

    def _create_database(self):
        self.connection = sqlite3.connect(self.db_file)
        cursor = self.connection.cursor()
        cursor.execute(CREATE_ARTICLES)
        self.connection.commit()

    def _connect_to_db(self):
        self.connection = sqlite3.connect(self.db_file)

    def update_rpc(self, local_id, status):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE articles set rpc=? WHERE id=?", (status, local_id))
        self.connection.commit()

    def update_fb(self, local_id, status):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE articles set fb=? WHERE id=?", (status, local_id))
        self.connection.commit()
