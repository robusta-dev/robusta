import logging
import os
import os.path
import colorlog


def init_logging():
    logging_level = os.environ.get("LOG_LEVEL", "INFO")
    logging_format = "%(log_color)s%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s"
    logging_datefmt = "%Y-%m-%d %H:%M:%S"

    if os.environ.get("ENABLE_COLORED_LOGS", "false").lower() == "true":
        print("setting up colored logging")
        colorlog.basicConfig(
            format=logging_format, level=logging_level, datefmt=logging_datefmt
        )
    else:
        print("setting up regular logging")
        logging.basicConfig(
            format=logging_format, level=logging_level, datefmt=logging_datefmt
        )

    logging.getLogger().setLevel(logging_level)
    for logger_name in ["werkzeug", "telethon"]:
        log = logging.getLogger(logger_name)
        log.setLevel(logging.ERROR)

    logging.info(f"logger initialized using {logging_level} log level")
