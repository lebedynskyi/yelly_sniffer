import logging
import ssl

import certifi
from wordpress_xmlrpc.methods import posts as wp_posts_api

from wordpress_xmlrpc import Client, WordPressPost

from src.data import DBArticle

logger = logging.getLogger(__name__)


class WordpressRpcApi:
    def __init__(self, config: dict[str, str]):
        ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
        self.config = config
        self.wp = Client(self.config["rpc_url"], self.config["rpc_user"], self.config["rpc_password"])

    def publish(self, entity):
        self._publish_one(entity)

    def _publish_one(self, entity: DBArticle) -> int:
        logger.debug("RPC Publish -  %s", entity.meta_title)

        wp_post = WordPressPost()
        wp_post.title = entity.meta_title
        wp_post.content = entity.article_body
        # wp_post.post_status = "publish"
        wp_post.post_status = "draft"

        # with open(entity.image, 'rb') as img:
        #     data = {'name': 'picture.jpg', 'type': 'image/jpeg', 'bits': xmlrpc.client.Binary(img.read())}
        #     uploaded_image = wp.call(UploadFile(data))
        #     wp_post.thumbnail = uploaded_image['id']

        post_id: int = self.wp.call(wp_posts_api.NewPost(wp_post))
        post: WordPressPost = self.wp.call(wp_posts_api.GetPost(post_id))
        if hasattr(post, "thumbnail") and not post.thumbnail:
            logger.info("No image after saving post. Try to fix it")

            try:
                self.fix_post(post_id)
            except:
                logger.info("Failed to fix post.")
                pass
        return post_id


    def fix_post(self, post_id: int):
        attachments = self.wp.call(wp_posts_api.GetPosts({
            "post_type": "attachment",
            "post_parent": post_id,
            "number": 100,
        }))
        logger.info("Attachments: %s", attachments)


