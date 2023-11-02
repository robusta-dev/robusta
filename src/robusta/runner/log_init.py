import logging
import os
import os.path

import colorlog
from pythonjsonlogger import jsonlogger

from robusta.core.model.env_vars import ENABLE_JSON_LOGGING


def init_logging():
    logging_level = os.environ.get("LOG_LEVEL", "INFO")
    logging_format = "%(log_color)s%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s"
    logging_datefmt = "%Y-%m-%d %H:%M:%S"

    print("setting up colored logging")
    colorlog.basicConfig(format=logging_format, level=logging_level, datefmt=logging_datefmt)

    logging.getLogger().setLevel(logging_level)
    for logger_name in ["werkzeug", "telethon"]:
        log = logging.getLogger(logger_name)
        log.setLevel(logging.ERROR)

    logging.info(f"logger initialized using {logging_level} log level")


def init_json_logging():

    print(f"JSON logging is enabled?: {ENABLE_JSON_LOGGING}")

    logging_level = os.environ.get("LOG_LEVEL", "INFO")
    # logging_format = "%(log_color)s%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s"
    # logging_datefmt = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger()
    logger.setLevel(logging_level)
    logHandler = logging.StreamHandler()

    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)-8s %(message)s")
    logHandler.setFormatter(formatter)

    logger.addHandler(logHandler)

    for logger_name_new in ["werkzeug", "telethon"]:
        specific_logger = logging.getLogger(logger_name_new)
        specific_logger.setLevel(logging.ERROR)

    logging.info("logger initialized using JSON logging")
