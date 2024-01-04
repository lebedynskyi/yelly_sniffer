import logging
import os.path

from src.api.facebook import FaceBookApi
from src.api.rpc import RpcApi
from src.api.telega import TelegramApi
from src.db import SQLiteDatabase
from src.handler import DatabaseUpdater
from src.tools import parse_args, init_logger, read_configs

logger = logging.getLogger(__name__)


def test():
    args = parse_args()
    wd = os.path.abspath(args.directory)
    init_logger(wd)
    logger.debug("Working directory is '%s'", wd)

    fb = FaceBookApi("firefox", None, wd, None, headless=False)
    fb._login()
    fb._post_message("☺️😘Привет девчонки. Делюсь рецептом 🖐🤚.. Ссылка в первом комментари👇👇👇",
                     "https://sweety-life.fun/wp-content/uploads/2024/01/1704353278_a43683d33b40f413228d54e3c6ed4a2f.jpg")


if __name__ == "__main__":
    print("------------- Welcome to Vetalll Auto -------------")
    args = parse_args()
    wd = os.path.abspath(args.directory)
    init_logger(wd)
    logger.debug("Working directory is '%s'", wd)

    config = read_configs(wd)

    database = SQLiteDatabase(wd, config["general"]["database"])
    db_updater = DatabaseUpdater(database, config["general"])

    if args.links:
        db_updater.process_links(args.links.split(","))
    elif args.sites:
        db_updater.process_sites(args.sites.split(","))

    if args.xmlrpc:
        try:
            rpc = RpcApi(database, config["xml_rpc"])
            rpc.publish_all()
        except BaseException as e:
            logger.exception("Unable to publish by rpc", e)
    else:
        logger.info("RPC Is not enabled")

    if args.facebook:
        try:
            fb = FaceBookApi("firefox", database, wd, config["general"], headless=True)
            published = fb.publish()
            if published is not None and args.telegram:
                telega = TelegramApi(config["telegram"])
                telega.send_success(published.title, published.own_url)
        except BaseException as e:
            logger.exception("Unable to publish by facebook", e)
            if args.telegram:
                telega = TelegramApi(config["telegram"])
                telega.send_error("Error fb publish", "None")
            exit(1)
    else:
        logger.info("Facebook is not enabled")

    logger.info("Successfully Finished")
