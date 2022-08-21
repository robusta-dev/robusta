from typing import Any
from pydantic import BaseModel
import secrets
import string
import traceback
import typer
import yaml
import jwt as JWT


def gen_secret(length: int) -> str:
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


def write_values_file(output_path: str, values: dict[str, Any]):
    with open(output_path, "w") as output_file:
        yaml.safe_dump(values, output_file, sort_keys=False)
        typer.secho(
            f"Saved configuration to {output_path} - save this file for future use!",
            fg="red",
        )


class RobustaUI(BaseModel):
    RELAY_HOST: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

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
    # anon key
    storeApiKey: str = ""
    slackClientId: str = "your-client-id"
    slackClientSecret: str = "your-client-secret"
    slackSigningSecret: str = "your-signing-secret"
    syncActionAllowedOrigins: str = ""
    provider: str = "none"

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
    ##SUPABASE
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
    SUPABASE_URL: str = ""  # Internal URL
    PUBLIC_REST_URL: str = ""  ## Studio Public REST endpoint - replace this if you intend to use Studio outside of localhost

    ## POSTGRES
    POSTGRES_PORT: int = 5432
    POSTGRES_STORAGE: str = "50Gi"
    POSTGRES_PASSWORD: str = gen_secret(12)

    SITE_URL: str = "https://platform.remediate.dev"  # callback target should point to the dash board
    ADDITIONAL_REDIRECT_URLS: str = ""

    ## AUTH

    DISABLE_SIGNUP: bool = False
    ## Email auth
    ENABLE_EMAIL_SIGNUP: bool = True
    ENABLE_EMAIL_AUTOCONFIRM: bool = True
    SMTP_ADMIN_EMAIL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 2500
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_SENDER_NAME: str = ""

    ## Phone auth
    ENABLE_PHONE_SIGNUP: bool = False
    ENABLE_PHONE_AUTOCONFIRM: bool = False

    ## KONG API endpoint ports
    KONG_HTTP_PORT: int = 8000
    KONG_HTTPS_PORT: int = 8443

    enableRelay: bool = True
    enableRobustaUI: bool = True


def gen_gke(domain: str):
    values = SelfHostValues()
    values.PROVIDER = "gke"
    values.DOMAIN = domain

    relayValues = RobustaRelay(domain=domain, anon_key=values.ANON_KEY, provider="gke")
    uiValues = RobustaUI(domain=domain, anon_key=values.ANON_KEY)

    values = values.dict()
    values["robusta-ui"] = uiValues.dict()
    values["robusta-relay"] = relayValues.dict()
    write_values_file("self_host_values.yaml", values)


def gen_none(domain: str):

    typer.echo("asdasd")


gen_provider_callbacks = {"": gen_none, "none": gen_none, "gke": gen_gke}


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

    try:
        gen_provider_callbacks[provider](domain)
    except KeyError:
        typer.secho(
            f'Invalid provider {provider}. options are "", "gke"',
            fg=typer.colors.RED,
        )
    except Exception:
        typer.echo(f"unexpected error")
        if debug:
            typer.secho(traceback.format_exc())
