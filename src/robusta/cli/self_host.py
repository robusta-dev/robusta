import json
import secrets
import string
import time
from typing import Any, Dict, Optional

import jwt as JWT
import typer
import yaml
from pydantic import BaseModel

from robusta.cli.backend_profile import BackendProfile

ISSUER: str = "supabase"


def issued_at() -> int:
    return int(time.time())


def gen_secret(length: int) -> str:
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))


def write_values_files(
    values_path: str,
    backendconfig_path: str,
    values: Dict[str, Any],
    backendProfile: BackendProfile,
):
    with open(values_path, "w") as output_file:
        yaml.safe_dump(values, output_file, sort_keys=False)
        typer.secho(
            f"Saved configuration to {values_path} - save this file for future use!",
            fg="red",
        )

    with open(backendconfig_path, "w") as output_file:
        json.dump(backendProfile.dict(exclude={"custom_profile"}), output_file, indent=1)
        typer.secho(
            f"Saved configuration to {backendconfig_path} - save this file for future use!",
            fg="red",
        )


class RobustaUI(BaseModel):
    RELAY_HOST: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    service = {"nodePort": 30311}  # platform.domain

    def __init__(self, domain: str, anon_key: str):
        super().__init__(
            RELAY_HOST=f"https://api.{domain}",
            SUPABASE_URL=f"https://db.{domain}",
            SUPABASE_KEY=anon_key,
        )


class RobustaRelay(BaseModel):
    domain: str
    storePassword: str
    storeUser: str = "apiuser-robustarelay@robusta.dev"
    storeUrl: str
    storeApiKey: str  # anon key
    slackClientId: str = "your-client-id"
    slackClientSecret: str = "your-client-secret"
    slackSigningSecret: str = "your-signing-secret"
    syncActionAllowedOrigins: str
    provider: str
    apiNodePort: int = 30313  # api.domain
    wsNodePort: int = 30314  # relay.domain

    def __init__(self, domain: str, anon_key: str, provider: str, storePW: str):
        super().__init__(
            domain=domain,
            storeUrl=f"https://db.{domain}",
            syncActionAllowedOrigins=f"https://platform.{domain}",
            storeApiKey=anon_key,
            provider=provider,
            storePassword=storePW,
        )


class SelfHostValues(BaseModel):
    STATIC_IP_NAME: str = "robusta-platform-ip"
    RELAY_PASSWORD: str = gen_secret(12)
    RELAY_USER: str = "apiuser-robustarelay@robusta.dev"
    DOMAIN: str
    PROVIDER: str
    # SUPABASE
    JWT_SECRET: str = gen_secret(32)
    ANON_KEY: str = JWT.encode(
        {"role": "anon", "iss": ISSUER, "iat": issued_at()},
        JWT_SECRET,
    )
    SERVICE_ROLE_KEY: str = JWT.encode(
        {
            "role": "service_role",
            "iss": ISSUER,
            "iat": issued_at(),
        },
        JWT_SECRET,
    )
    SUPABASE_URL: str = "http://kong:8000"  # Internal URL
    PUBLIC_REST_URL: str  # Studio Public REST endpoint - replace this if you intend to use Studio outside of localhost

    # POSTGRES
    POSTGRES_PORT: int = 5432
    POSTGRES_STORAGE: str = "100Gi"
    POSTGRES_PASSWORD: str = gen_secret(12)
    STORAGE_CLASS_NAME: Optional[str] = None
    EKS_CERTIFICATE_ARN: Optional[str] = None

    SITE_URL: str  # callback target should point to the dash board
    ADDITIONAL_REDIRECT_URLS: str = ""

    # KONG API endpoint ports
    KONG_HTTP_PORT: int = 8000
    KONG_HTTP_NODE_PORT: int = 30312  # db.domain
    KONG_HTTPS_PORT: int = 8443

    enableRelay: bool = True
    enableRobustaUI: bool = True


app = typer.Typer(add_completion=False)


@app.command()
def gen_config(
    provider: str = typer.Option(
        ...,
        help='Cloud host provider. options are "on-prem", "gke", "eks"',
    ),
    domain: str = typer.Option(..., help="domain used to route the on-prem services."),
    storage_class_name: str = typer.Option(None, help="database PVC storageClassName."),
    eks_certificate_arn: str = typer.Option(None, help="certificate arn for EKS ingress"),
    platform_nport: int = typer.Option(30311, help="node port for the Robusta dashboard."),
    db_nport: int = typer.Option(30312, help="node port Robusta database."),
    api_nport: int = typer.Option(30313, help="node port for Robusta API."),
    ws_nport: int = typer.Option(30314, help="node port for Robusta websocket."),
):
    """Create self host configuration files"""
    if provider not in {"on-prem", "gke", "eks"}:
        typer.secho(
            f'Invalid provider {provider}. options are "on-prem", "gke", "eks"',
            fg=typer.colors.RED,
        )
        return

    if not domain:
        typer.secho(
            "Missing required argument domain",
            fg=typer.colors.RED,
        )
        return

    values = SelfHostValues(
        PROVIDER=provider,
        DOMAIN=domain,
        SITE_URL=f"https://platform.{domain}",
        PUBLIC_REST_URL=f"https://db.{domain}/rest/v1/",
        STORAGE_CLASS_NAME=storage_class_name,
        EKS_CERTIFICATE_ARN=eks_certificate_arn,
    )
    values.KONG_HTTP_NODE_PORT = db_nport

    relayValues = RobustaRelay(
        domain=domain,
        anon_key=values.ANON_KEY,
        provider=provider,
        storePW=values.RELAY_PASSWORD,
    )
    relayValues.apiNodePort = api_nport
    relayValues.wsNodePort = ws_nport

    uiValues = RobustaUI(domain=domain, anon_key=values.ANON_KEY)
    uiValues.service["nodePort"] = platform_nport

    values_dict = values.dict(exclude_none=True)
    values_dict["robusta-ui"] = uiValues.dict()
    values_dict["robusta-relay"] = relayValues.dict()

    backendProfile = BackendProfile.fromDomain(domain=domain)
    self_host_approval_url = "https://api.robusta.dev/terms-of-service.html"
    typer.echo(f"By using this software you agree to the terms of service ({self_host_approval_url})\n")
    write_values_files("self_host_values.yaml", "robusta_cli_config.json", values_dict, backendProfile)
