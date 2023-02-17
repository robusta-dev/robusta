import base64
import os

import certifi


def add_custom_certificate(custom_ca: str):

    if custom_ca:
        with open(certifi.where(), "ab") as outfile:
            outfile.write(base64.b64decode(custom_ca))
            os.environ["WEBSOCKET_CLIENT_CA_BUNDLE"] = certifi.where()
            return True

    return False
