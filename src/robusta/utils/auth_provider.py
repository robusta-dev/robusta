import logging
import os
from typing import Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from ..core.model.env_vars import RSA_KEYS_PATH


class AuthProvider:

    def __init__(self):
        logging.info(f"Loading RSA keys from {RSA_KEYS_PATH}")
        self.prv: RSAPrivateKey = self.__class__._load_private_key(os.path.join(RSA_KEYS_PATH, "prv"))
        self.pub: RSAPublicKey = self.__class__._load_public_key(os.path.join(RSA_KEYS_PATH, "pub"))

    def get_private_rsa_key(self) -> RSAPrivateKey:
        return self.prv

    def get_public_rsa_key(self) -> RSAPublicKey:
        return self.pub

    @staticmethod
    def _load_private_key(file_name: str) -> Optional[RSAPrivateKey]:
        try:
            with open(file_name, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                )
                logging.info(f"Loaded private key file {file_name}")
                return private_key
        except Exception:
            logging.error(f"Could not load private key file {file_name}")

        return None

    @staticmethod
    def _load_public_key(file_name: str) -> Optional[RSAPublicKey]:
        try:
            with open(file_name, "rb") as key_file:
                public_key = serialization.load_pem_public_key(key_file.read())
                logging.info(f"Loaded public key file {file_name}")
                return public_key
        except Exception:
            logging.error(f"Could not load public key file {file_name}")

        return None
