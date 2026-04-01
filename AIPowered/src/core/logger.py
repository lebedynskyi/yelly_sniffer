import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from src.core.cli import ParsedArgs


def init_logger(args: ParsedArgs):
    out_folder = args.workdir

    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    formatter = logging.Formatter(fmt="%(asctime)s: %(name)s: %(levelname)s %(message)s")
    console_info_handler = logging.StreamHandler(sys.stdout)
    console_info_handler.level = logging.DEBUG
    console_info_handler.setFormatter(formatter)

    log_file = os.path.join(out_folder, "logs.log")
    file_handler = RotatingFileHandler(filename=log_file, maxBytes=int(0.25 * 1024 * 1024),
                                       mode='a', backupCount=5, encoding="utf-8", delay=False)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logging.basicConfig(encoding="utf-8", level=logging.DEBUG, handlers=[console_info_handler, file_handler])

    logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("filelock").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("google_genai.models").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)

    logger = logging.getLogger()

    logger.info("Logger initialized")
