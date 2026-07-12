import logging
import os
import os.path
import sys

import colorlog
from pythonjsonlogger.json import JsonFormatter

from robusta.core.model.env_vars import ENABLE_JSON_LOGS_FORMAT


def init_logging():
    logging_level = os.environ.get("LOG_LEVEL", "INFO")
    logging_datefmt = "%Y-%m-%d %H:%M:%S"

    if ENABLE_JSON_LOGS_FORMAT:
        # JSON logs (one object per line) are easier for log scrapers like
        # Filebeat to index, search, and filter. Rename levelname -> severity
        # to match the convention used across Robusta services (relay, holmes).
        print("setting up json logging")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            JsonFormatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(filename)s %(lineno)d %(funcName)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
                rename_fields={"levelname": "severity"},
            )
        )
        logging.basicConfig(handlers=[handler], level=logging_level, force=True)
    else:
        logging_format = "%(log_color)s%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s"
        print("setting up colored logging")
        colorlog.basicConfig(format=logging_format, level=logging_level, datefmt=logging_datefmt)

    logging.getLogger().setLevel(logging_level)
    for logger_name in ["werkzeug", "telethon"]:
        log = logging.getLogger(logger_name)
        log.setLevel(logging.ERROR)

    logging.info(f"logger initialized using {logging_level} log level")
