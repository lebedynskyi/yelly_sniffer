import logging

from src.ai.ai_fixer import LLMFixer, GeminiFixer
from src.crawl import Crawler
from src.core import cli, config
from src.core.logger import init_logger
from src.data import SQLiteDatabase
from src.sanitizer import Bs4HtmlSanitizer
from src.updater import Updater
from src.xml_rpc import WordpressRpcApi

logger = None

if __name__ == "__main__":
    args = cli.parse_args()
    init_logger(args)

    logger = logging.getLogger()
    configs = config.read_configs(args.workdir)

    logging.info("🪄Magic is started")

    crawler = Crawler(args.workdir, configs)
    database = SQLiteDatabase(args.workdir)
    sanitizer = Bs4HtmlSanitizer()
    fixer = LLMFixer(args.workdir)
    fixer_gemini = GeminiFixer(configs["ai"]["gemini_api_key"])
    wp_rpc = WordpressRpcApi(configs["xml_rpc"])

    updater = Updater(database, crawler, sanitizer, fixer_gemini, wp_rpc)
    updater.process(args)
    logger.info("🪄Magic is finished")
    exit(0)

    # wp_rpc.fix_post(13848)

    # article = database.find_by_fb_status(False)[0]
    # fb_auto = FBAuto(args.workdir, configs["facebook"])
    # fb_auto.publish_post(article)



# https://dzen.ru/historygothy,https://dzen.ru/verynevery,https://dzen.ru/annamednikovablog,https://dzen.ru/psychology_of_horror

# https://storyx.ru

# https://dzen.ru/life_matters,https://dzen.ru/russstories.ru