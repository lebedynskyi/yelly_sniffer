import logging
import os

import yaml

logger = logging.getLogger(__name__)


def read_configs(out_directory) -> dict[str, dict[str, str]]:
    logger.info("⚙️Reading config")
    config_file = os.path.join(out_directory, "config.yaml")
    if not os.path.exists(config_file):
        logger.error("Error: Unable to locate config file '%s'", config_file)
        exit(1)

    with open(config_file, "r") as file_object:
        config = yaml.load(file_object, Loader=yaml.SafeLoader)

    logger.info("⚙️Reading config successfully")
    return config
