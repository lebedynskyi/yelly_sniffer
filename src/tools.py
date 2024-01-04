import argparse
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import yaml

logger = logging.getLogger(__name__)


def init_logger(out_folder):
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    # TODO add log level to text
    formatter = logging.Formatter(fmt="%(asctime)s: %(name)s: %(message)s")
    console_info_handler = logging.StreamHandler(sys.stdout)
    console_info_handler.level = logging.DEBUG
    console_info_handler.setFormatter(formatter)

    log_file = os.path.join(out_folder, "logs.log")
    file_handler = RotatingFileHandler(filename=log_file, maxBytes=int(0.5 * 1024 * 1024),
                                       mode='a', backupCount=5, encoding="utf-8", delay=False)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logging.basicConfig(encoding="utf-8", level=logging.DEBUG, handlers=[console_info_handler, file_handler])

    logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

    logger.info("Logger initialized")


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--links", help="list of links comma separated", required=False)
    parser.add_argument("-s", "--sites", help="list of sites comma separated", required=False)
    parser.add_argument("-d", "--directory", help="Working directory where config.ini", default="output")
    parser.add_argument('-f', "--facebook", help="Enable facebook posting", action='store_true', required=False,
                        default=False)
    parser.add_argument('-t', "--telegram", help="Enable telegram posting", action='store_true', required=False,
                        default=False)
    parser.add_argument('-x', "--xmlrpc", help="Enable xmlrpc posting", action='store_true', required=False,
                        default=False)
    return parser.parse_args()


def read_configs(out_directory):
    config_file = os.path.join(out_directory, "config.yaml")
    if not os.path.exists(config_file):
        logger.error("Error: Unable to locate config file '%s'", config_file)
        exit(1)

    with open(config_file, "r") as file_object:
        config = yaml.load(file_object, Loader=yaml.SafeLoader)
    return config
