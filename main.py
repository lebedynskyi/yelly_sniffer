import logging
import os.path

from src.api.facebook import FaceBookApi
from src.api.rpc import RpcApi
from src.api.telega import TelegramApi
from src.api.yelly import YellyApi
from src.db import SQLiteDatabase
from src.handler import DatabaseUpdater
from src.tools import parse_args, init_logger, read_configs

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    print("------------- Welcome to Vetalll Auto -------------")
    args = parse_args()
    wd = os.path.abspath(args.directory)
    init_logger(wd)
    logger.debug("Working directory is '%s'", wd)

    config = read_configs(wd)

    yelly = YellyApi()
    database = SQLiteDatabase(wd, config["general"]["database"])
    db_updater = DatabaseUpdater(database, yelly, config["general"])

    if args.links:
        db_updater.process_links(args.links.split(","))
    elif args.sites:
        db_updater.process_sites(args.sites.split(","))
    else:
        logger.error("Nothing to do. No '-s/--sites' or '-l/--links' arguments provided")
        exit(1)

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
