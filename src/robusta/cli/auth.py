import base64
import json
import subprocess
import traceback
import uuid
from typing import Optional
import click_spinner
from dpath.util import get
import requests
import typer
import yaml
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import BaseModel

from .backend_profile import backend_profile
from .playbooks_cmd import NAMESPACE_EXPLANATION, get_playbooks_config
from .utils import namespace_to_kubectl

AUTH_SECRET_NAME = "robusta-auth-config-secret"
app = typer.Typer()


class RSAKeyPair(BaseModel):
    prv: str
    pub: str


def gen_rsa_pair() -> RSAKeyPair:
    # generate private/public key pair
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # get public key in OpenSSH format
    public_key = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    # get private key in PEM container format
    pem = key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption()
    )

    return RSAKeyPair(
        pub=public_key.decode('utf-8'),
        prv=pem.decode('utf-8')
    )


def get_existing_auth_config(namespace: str) -> Optional[RSAKeyPair]:
    try:
        secret_content = subprocess.check_output(
            f"kubectl get secret {namespace_to_kubectl(namespace)} {AUTH_SECRET_NAME} -o yaml",
            shell=True,
        )
    except Exception:
        return None

    auth_secret = yaml.safe_load(secret_content)
    return RSAKeyPair(
        prv=base64.b64decode(auth_secret["data"]["prv"]).decode(),
        pub=base64.b64decode(auth_secret["data"]["pub"]).decode()
    )


class TokenDetails(BaseModel):
    pub: str
    account_id: str
    user_id: str
    session_token: str
    enc_key: str
    key_id: str


def store_server_token(token_details: TokenDetails, debug: bool = False) -> bool:
    try:
        response = requests.post(backend_profile.robusta_store_token_url, json=token_details.dict())
        if debug and response.status_code != 201:
            typer.secho(f"Failed to store server token. status-code {response.status_code} text {response.text}")

        return response.status_code == 201
    except Exception as e:
        if debug:
            typer.secho(f"Error trying to store server token. {traceback.format_exc()}")
        return False


@app.command()
def gen_token(
    account_id: str = typer.Option(
        ...,
        help="Robusta account id",
    ),
    user_id: str = typer.Option(
        ...,
        help="User id for which the token is created",
    ),
    session_token: str = typer.Option(
        ...,
        help="User session token. Created for an authenticated user via the Robusta UI",
    ),
    namespace: str = typer.Option(
        None,
        help=NAMESPACE_EXPLANATION,
    ),
    debug: bool = typer.Option(False),
):
    """Generate token required to run actions manually in Robusta UI"""
    typer.echo("connecting to cluster...")
    with click_spinner.spinner():
        auth_config = get_existing_auth_config(namespace)

    if not auth_config:
        typer.secho("\nRSA auth isn't configured. "
                    "Please update Robusta and run `robusta update-config` to configure it. Aborting!", fg="red")
        return

    playbooks_config = get_playbooks_config(namespace)
    active_playbooks_file = playbooks_config["data"]["active_playbooks.yaml"]
    playbooks_config_yaml = yaml.safe_load(active_playbooks_file)
    signing_key = get(playbooks_config_yaml, "global_config/signing_key", default=None)
    if not signing_key:
        typer.secho("signing_key is not defined. Please update Robusta and run `robusta update-config`", fg="red")
        return

    try:
        signing_key = uuid.UUID(signing_key)
    except Exception:
        typer.secho("Bad format for signing_key. Please run `robusta update-config` to generate a new valid"
                    " signing_key for your account.", fg="red")
        return

    client_enc_key = uuid.uuid4()
    server_enc_key = uuid.UUID(int=(signing_key.int ^ client_enc_key.int))
    key_id = str(uuid.uuid4())

    token_response = TokenDetails(
        pub=auth_config.pub,
        account_id=account_id,
        user_id=user_id,
        session_token=session_token,
        enc_key=str(server_enc_key),
        key_id=key_id,
    )
    if not store_server_token(token_response, debug):
        typer.secho("Failed to store server token. Aborting!", fg="red")
        return

    # client response is the same, only with a different enc_key
    token_response.enc_key = str(client_enc_key)

    typer.secho(f"Token created successfully. Submit it in the Robusta UI", fg="green")
    typer.secho(base64.b64encode(token_response.json(exclude={"session_token"}).encode("utf-8")).decode())
