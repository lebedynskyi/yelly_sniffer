import logging

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import posts as wp_posts_api

logger = logging.getLogger(__name__)


class RpcApi:
    def __init__(self, database, config):
        self.database = database
        self.config = config

    def publish(self, post_ids):
        entities = self.database.find_with_rpc_status(post_ids, False)

        if not entities:
            logger.debug("RPC No posts found or everything is up to date")
            return

        for entity in entities:
            self._publish_one(entity)

    def _publish_one(self, entity):
        wp = Client(self.config["rpc_url"], self.config["rpc_user"], self.config["rpc_password"])
        logger.debug("RPC Publish -  %s", entity.title)

        try:
            wp_post = WordPressPost()
            wp_post.title = entity.title
            wp_post.content = entity.orig_content
            wp_post.post_status = "publish"

            # with open(entity.image, 'rb') as img:
            #     data = {'name': 'picture.jpg', 'type': 'image/jpeg', 'bits': xmlrpc.client.Binary(img.read())}
            #     uploaded_image = wp.call(UploadFile(data))
            #     wp_post.thumbnail = uploaded_image['id']

            post_id = wp.call(wp_posts_api.NewPost(wp_post))
            published = wp.call(wp_posts_api.GetPost(post_id))
            entity.own_url = published.link
            entity.own_content = published.content
            if published.thumbnail:
                entity.image = published.thumbnail["link"]
            entity.rpc_status = 1
        except BaseException as e:
            raise e
        finally:
            self.database.update_rpc_status(entity.local_id, entity.own_url, entity.image, 1)
