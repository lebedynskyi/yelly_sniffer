import logging
import os.path

from src.db import SQLiteDatabase
from src.processor import process_updater, process_rpc, process_facebook, process_telega
from src.tools import parse_args, init_logger, read_configs

logger = logging.getLogger(__name__)

POST_COUNT = 1
RETRY_COUNT = 1


def debug():
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

    post_ids = None
    if app_args.links:
        post_ids = process_updater(app_args, app_database, app_config["general"], links=app_args.links.split(","))
    elif app_args.sites:
        post_ids = process_updater(app_args, app_database, app_config["general"], sites=app_args.sites.split(","))
    else:
        logger.info("Updater is not enabled. No -s/--sites -l/--links arguments provided")

    if app_args.xmlrpc and post_ids:
        process_rpc(app_database, app_config["xml_rpc"], post_ids)
    else:
        logger.info("RPC Is not enabled. No -x arguments provided")

    published = None
    if app_args.facebook:
        published = process_facebook(app_database, app_wd, app_config["facebook"], post_ids)
    else:
        logger.info("Facebook is not enabled. No -f arguments provided")

    if app_args.telegram:
        process_telega(app_config["telegram"], published)
    else:
        logger.info("Telegram is not enabled. No -t argument provided")


if __name__ == "__main__":
    print("------------- Welcome to FB Auto -------------")
    counter = 0
    while counter < RETRY_COUNT:
        try:
            logger.info(f"------------- FB Auto Retry {counter} -------------\n")
            main()
        except BaseException as e:
            logger.error("Error during automation, %s", e)
            counter = counter + 1

    logger.info(f"------------- FB Auto Finish -------------\n")
    exit()
