import secrets
import string
import typer
import yaml
import json
from typing import Any
from pydantic import BaseModel
from .backend_profile import BackendProfile
import jwt as JWT


def gen_secret(length: int) -> str:
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


def write_values_files(
    values_path: str,
    backendconfig_path: str,
    values: dict[str, Any],
    backendProfile: BackendProfile,
):
    with open(values_path, "w") as output_file:
        yaml.safe_dump(values, output_file, sort_keys=False)
        typer.secho(
            f"Saved configuration to {values_path} - save this file for future use!",
            fg="red",
        )

    with open(backendconfig_path, "w") as output_file:
        json.dump(
            backendProfile.dict(exclude={"custom_profile"}), output_file, indent=1
        )
        typer.secho(
            f"Saved configuration to {backendconfig_path} - save this file for future use!",
            fg="red",
        )


class RobustaUI(BaseModel):
    RELAY_HOST: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    service = {"nodePort": 30311}  # platform.domain

    def __init__(self, domain: str, anon_key: str):
        super().__init__(
            RELAY_HOST=f"https://api.{domain}",
            SUPABASE_URL=f"https://db.{domain}",
            SUPABASE_KEY=anon_key,
        )


class RobustaRelay(BaseModel):
    domain: str = ""
    storePassword: str = gen_secret(12)
    storeUser: str = "apiuser-robustarelay@robusta.dev"
    storeUrl: str = ""
    storeApiKey: str = ""  # anon key
    slackClientId: str = "your-client-id"
    slackClientSecret: str = "your-client-secret"
    slackSigningSecret: str = "your-signing-secret"
    syncActionAllowedOrigins: str = ""
    provider: str = ""
    apiNodePort: int = 30313  # api.domain
    wsNodePort: int = 30314  # relay.domain

    def __init__(self, domain: str, anon_key: str, provider: str):
        super().__init__(
            domain=domain,
            storeUrl=f"https://db.{domain}",
            syncActionAllowedOrigins=f"https://platform.{domain}",
            storeApiKey=anon_key,
            provider=provider,
        )


class SelfHostValues(BaseModel):
    DOMAIN: str = ""
    PROVIDER: str = ""
    # SUPABASE
    JWT_SECRET: str = gen_secret(32)
    JWT_EXPIRY: int = 3600
    ANON_KEY: str = JWT.encode(
        {"role": "anon", "iss": "supabase", "iat": 1661029200, "exp": 1818795600},
        JWT_SECRET,
    )
    SERVICE_ROLE_KEY: str = JWT.encode(
        {
            "role": "service_role",
            "iss": "supabase",
            "iat": 1661029200,
            "exp": 1818795600,
        },
        JWT_SECRET,
    )
    SUPABASE_URL: str = "http://kong:8000"  # Internal URL
    PUBLIC_REST_URL: str = ""  ## Studio Public REST endpoint - replace this if you intend to use Studio outside of localhost

    # POSTGRES
    POSTGRES_PORT: int = 5432
    POSTGRES_STORAGE: str = "50Gi"
    POSTGRES_PASSWORD: str = gen_secret(12)

    SITE_URL: str = ""  # callback target should point to the dash board
    ADDITIONAL_REDIRECT_URLS: str = ""

    DISABLE_SIGNUP: bool = False
    # Email auth
    ENABLE_EMAIL_SIGNUP: bool = True
    ENABLE_EMAIL_AUTOCONFIRM: bool = True
    SMTP_ADMIN_EMAIL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 2500
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_SENDER_NAME: str = ""

    # Phone auth
    ENABLE_PHONE_SIGNUP: bool = False
    ENABLE_PHONE_AUTOCONFIRM: bool = False

    # KONG API endpoint ports
    KONG_HTTP_PORT: int = 8000
    KONG_HTTP_NODE_PORT: int = 30312  # db.domain
    KONG_HTTPS_PORT: int = 8443

    enableRelay: bool = True
    enableRobustaUI: bool = True


app = typer.Typer()


@app.command()
def gen_config(
    provider: str = typer.Option(
        "",
        help="Cloud host provider.",
    ),
    domain: str = typer.Option("", help="domain used to route the self host services."),
    debug: bool = typer.Option(False),
):
    """Create self host configuration file"""

    if provider not in {"", "gke"}:
        typer.secho(
            f'Invalid provider {provider}. options are "", "gke"',
            fg=typer.colors.RED,
        )
        return

    values = SelfHostValues(
        PROVIDER=provider,
        DOMAIN=domain,
        SITE_URL=f"https://platform.{domain}",
        PUBLIC_REST_URL=f"https://db.{domain}/rest/v1/",
    )

    relayValues = RobustaRelay(
        domain=domain, anon_key=values.ANON_KEY, provider=provider
    )
    uiValues = RobustaUI(domain=domain, anon_key=values.ANON_KEY)

    values = values.dict()
    values["robusta-ui"] = uiValues.dict()
    values["robusta-relay"] = relayValues.dict()

    backendProfile = BackendProfile.fromDomain(domain=domain)
    write_values_files(
        "self_host_values.yaml", "robusta_cli_config.json", values, backendProfile
    )
