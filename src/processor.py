import logging

from src.api.facebook import FaceBookApi
from src.api.rpc import RpcApi
from src.api.telega import TelegramApi
from src.models import PostEntity
from src.updater import DatabaseUpdater

logger = logging.getLogger(__name__)


def process_updater(args, database, config, links=None, sites=None):
    db_updater = DatabaseUpdater(database, config)

    if args.links:
        return db_updater.process_links(links)
    elif args.sites:
        return db_updater.process_sites(sites)
    else:
        return None


def process_rpc(database, config, post_ids):
    try:
        rpc = RpcApi(database, config)
        return rpc.publish(post_ids)
    except BaseException as e:
        logger.exception("Unable to publish by rpc", e)


def process_facebook(database, directory, config, post_ids):
    try:
        fb = FaceBookApi(database, directory, config)
        return fb.publish(post_ids)
    except BaseException as e:
        logger.exception("Unable to publish by facebook", e)


def process_telega(config, data):
    telega = TelegramApi(config)

    if data is PostEntity:
        telega.send_success(data.title, data.own_url)
    elif data is BaseException:
        telega.send_error(data)
    else:
        logger.info("Unknown telegram data. Data is %s", data)

