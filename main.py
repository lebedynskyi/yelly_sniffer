import logging
import os.path

from src.api.facebook import FaceBookApi
from src.db import SQLiteDatabase
from src.processor import process_updater, process_rpc, process_facebook, process_telega
from src.tools import parse_args, init_logger, read_configs

logger = logging.getLogger(__name__)


def test():
    args = parse_args()
    wd = os.path.abspath(args.directory)
    init_logger(wd)
    logger.debug("Working directory is '%s'", wd)
    #
    # fb = FaceBookApi("firefox", None, wd, None, headless=False)
    # fb._login()
    # fb._post_message("☺️😘Привет девчонки. Делюсь рецептом 🖐🤚.. Ссылка в первом комментари👇👇👇",
    #                  "https://sweety-life.fun/wp-content/uploads/2024/01/1704353278_a43683d33b40f413228d54e3c6ed4a2f.jpg")


def main():
    app_args = parse_args()
    app_wd = os.path.abspath(app_args.directory)
    init_logger(app_wd)
    logger.debug("Working directory is '%s'", app_wd)
    app_config = read_configs(app_wd)
    app_database = SQLiteDatabase(app_wd, app_config["general"]["database"])

    # TODO extract configs from args. Pass just config dict

    if app_args.links:
        process_updater(app_args, app_database, app_config, links=app_args.links.split(","))
    elif app_args.sites:
        process_updater(app_args, app_database, app_config, sites=app_args.sites.split(","))
    else:
        logger.info("Updater is not enabled. No -s/--sites -l/--links arguments provided")

    if app_args.xmlrpc:
        # TODO add rpc count argument https://stackoverflow.com/questions/30896982/argparse-optional-value-for-argument
        process_rpc(app_database, app_config, count=1)
    else:
        logger.info("RPC Is not enabled")

    published = None
    if app_args.facebook:
        published = process_facebook(app_database, app_wd, app_config)
    else:
        logger.info("Facebook is not enabled")

    if app_args.telegram:
        process_telega(app_config, published)
    else:
        logger.info("Telegram is not enabled")


if __name__ == "__main__":
    print("------------- Welcome to Vetalll Auto -------------")
    try:
        main()
    except BaseException as e:
        logger.error("Error during automation", e)
    logger.info("------------- Finish Vetalll Auto -------------\n")
    exit(0)
