import logging

from src.api.facebook import FaceBookApi
from src.api.rpc import RpcApi
from src.api.telega import TelegramApi
from src.models import PostEntity
from src.updater import DatabaseUpdater

logger = logging.getLogger(__name__)


def process_updater(args, database, config, driver, links=None, sites=None):
    db_updater = DatabaseUpdater(database, config["general"])

    if args.links:
        db_updater.process_links(links, driver)

    if args.sites:
        db_updater.process_sites(sites, driver)


def process_rpc(database, config, count):
    try:
        rpc = RpcApi(database, config["xml_rpc"])
        return rpc.publish(count)
    except BaseException as e:
        logger.exception("Unable to publish by rpc", e)


def process_facebook(database, directory, config, driver):
    try:
        fb = FaceBookApi(driver, database, directory, config["facebook"])
        return fb.publish()
    except BaseException as e:
        logger.exception("Unable to publish by facebook", e)


def process_telega(config, data):
    telega = TelegramApi(config["telegram"])

    if data is PostEntity:
        telega.send_success(data.title, data.own_url)
    elif data is BaseException:
        telega.send_error(data)
    else:
        logger.info("Unknown telegram data. Data is %s", data)

