import logging

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import posts as wp_posts_api
from wordpress_xmlrpc.methods import users as wp_users_api

logger = logging.getLogger(__name__)


class RpcApi:
    def __init__(self, database, config):
        self.database = database
        self.config = config

    def publish_all(self):
        entities = self.database.find_by_rpc_status(False)
        if not entities:
            logger.debug("RPC everything is up to date")
            return

        wp = Client(self.config["rpc_url"], self.config["rpc_user"], self.config["rpc_password"])
        user = wp.call(wp_users_api.GetUserInfo())
        if not user:
            logger.debug("RPC Unable to connect to RPC server")
            return None

        logger.debug("RPC Connected successfully. User is %s", user.username)
        for entity in entities:
            logger.debug("RPC Publish -  %s", entity.title)

            try:
                wp_post = WordPressPost()
                wp_post.title = entity.title
                wp_post.content = entity.orig_content
                wp_post.post_status = "publish"

                # with open(p.image, 'rb') as img:
                #     data = {'name': 'picture.jpg', 'type': 'image/jpeg', 'bits': xmlrpc_client.Binary(img.read())}
                #     uploaded_image = wp.call(wp_media_api.UploadFile(data))
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
