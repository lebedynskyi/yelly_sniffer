import logging
import os.path
import sqlite3
from collections.abc import Iterable
from datetime import datetime

from src.models import PostEntity

logger = logging.getLogger(__name__)


class SQLiteDatabase:
    connection = None

    def __init__(self, wd, db_name):
        self.wd = wd
        self.db_file = os.path.join(wd, db_name)
        if not os.path.exists(self.db_file):
            logger.info("Database '%s' not exist. Create it", self.db_file)
            self.create_database()
        else:
            self.connect_to_db()

    def insert_new_post(self, posts):
        cursor = self.connection.cursor()

        if not isinstance(posts, Iterable):
            posts = [posts]

        ids = []

        for p in posts:
            cursor.execute(
                "INSERT INTO posts(title, orig_content, orig_url, thumbnail, date) VALUES (?,?,?,?,?)",
                (p.title, p.body, p.orig_url, p.image, datetime.now())
            )
            ids.append(cursor.lastrowid)

        self.connection.commit()
        return ids

    def exist(self, title):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM posts where title=?", (title,))
        return cursor.fetchone() is not None

    def find_with_rpc_status(self, post_ids, rpc_status):
        cursor = self.connection.cursor()
        placeholders = ",".join("?" for _ in post_ids)
        cursor.execute(f"SELECT * FROM posts where rpc_publish=? AND id IN ({placeholders}) ORDER BY date DESC", (rpc_status, *post_ids))
        res = cursor.fetchall()
        return [PostEntity(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]) for r in res]

    def find_with_fb_status(self, fb_status, rpc_status, post_ids):
        cursor = self.connection.cursor()
        placeholders = ",".join("?" for _ in post_ids)
        cursor.execute(f"SELECT * FROM posts where fb_publish=? AND rpc_publish=? AND id IN ({placeholders}) ORDER BY date DESC", (fb_status, rpc_status, *post_ids))
        res = cursor.fetchall()
        return [PostEntity(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]) for r in res]

    def update_rpc_status(self, local_id, own_url, image, rpc_status):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE posts set own_url=?, thumbnail=?, rpc_publish=? WHERE id=?",
                       (own_url, image, rpc_status, local_id))
        self.connection.commit()

    def update_fb_status(self, local_id, fb_status):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE posts set fb_publish=? WHERE id=?",
                       (fb_status, local_id))
        self.connection.commit()

    def create_database(self):
        self.connection = sqlite3.connect(self.db_file)
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE TABLE posts(id INTEGER PRIMARY KEY AUTOINCREMENT, date INTEGER, title TEXT, orig_content TEXT, orig_url TEXT, own_url TEXT, thumbnail TEXT, fb_publish INTEGER DEFAULT 0, rpc_publish INTEGER DEFAULT 0)")
        self.connection.commit()

    def get_last_fb_publish_date(self):
        with open(os.path.join(self.wd, "last_fb.date.txt"), 'r') as file:
            return datetime.strptime(file.read(), "%d-%b-%Y (%H:%M:%S.%f)")

    def save_last_fb_publish_date(self):
        with open(os.path.join(self.wd, "last_fb.date.txt"), 'w') as file:
            file.write(datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"))

    def connect_to_db(self):
        self.connection = sqlite3.connect(self.db_file)
