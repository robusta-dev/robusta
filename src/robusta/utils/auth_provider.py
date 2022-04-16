import logging
import os
from typing import Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from ..core.model.env_vars import RSA_KEYS_PATH


class AuthProvider:
    pub: RSAPublicKey = None
    prv: RSAPrivateKey = None

    @classmethod
    def get_private_rsa_key(cls) -> RSAPrivateKey:
        return cls.prv

    @classmethod
    def get_public_rsa_key(cls) -> RSAPublicKey:
        return cls.pub

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
                public_key = serialization.load_ssh_public_key(key_file.read())
                logging.info(f"Loaded public key file {file_name}")
                return public_key
        except Exception:
            logging.error(f"Could not load public key file {file_name}")

        return None

    @classmethod
    def _load_rsa_keys(cls):
        logging.info(f"Loading RSA keys from {RSA_KEYS_PATH}")
        cls.prv = cls._load_private_key(os.path.join(RSA_KEYS_PATH, "prv"))
        cls.pub = cls._load_public_key(os.path.join(RSA_KEYS_PATH, "pub"))

AuthProvider._load_rsa_keys()
