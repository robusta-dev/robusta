import base64
import logging


def is_base64_encoded(value: str) -> bool:
    try:
        if base64.b64encode(base64.b64decode(value)) == bytes(value, 'utf-8'):  # key is b64
            return True
        else:
            return False
    except Exception as e:
        logging.error("Error during base64 check")
        logging.exception(e)
        return False
