import base64
import logging


def is_base64_encoded(value: str) -> bool:
    try:
        return base64.b64encode(base64.b64decode(value)) == bytes(value, 'utf-8') # value is b64
    except Exception as e:
        return False
