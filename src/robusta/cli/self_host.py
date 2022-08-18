from pydantic import BaseModel
import secrets
import string
import traceback
import typer


def gen_secret(length: int) -> str:
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


# PROVIDER: str = ""
# STATIC_IP_NAME: relay-test


class Domains(BaseModel):
    relay_api: str = ""
    relay_ws: str = ""
    ui: str = ""
    supabase: str = ""


class Supabase(BaseModel):
    JWT_SECRET: str = gen_secret(32)
    JWT_EXPIRY: int = 3600
    ANON_KEY: str = ""
    SERVICE_ROLE_KEY: str = ""
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


class RobustaUI(BaseModel):
    SUPABASE_URL: str = ""
    RELAY_HOST: str = ""
    # anon key
    SUPABASE_KEY: str = ""


class RobustaRelay(BaseModel):
    domain: str = ""
    storePassword: str = ""
    storeUser: str = "apiuser-robustarelay@robusta.dev"
    storeUrl: str = "https://db.remediate.dev"
    # anon key
    storeApiKey: str = ""
    slackClientId: str = "your-client-id"
    slackClientSecret: str = "your-client-secret"
    slackSigningSecret: str = "your-signing-secret"
    syncActionAllowedOrigins: str = "https://platform.remediate.dev"
    provider: str = ""


def gen_gke():
    typer.echo("gke")


def gen_none():
    typer.echo("none")


gen_provider_callbacks = {"": gen_none, "none": gen_none, "gke": gen_gke}


app = typer.Typer()


@app.command()
def gen_config(
    provider: str = typer.Option(
        "",
        help="Cloud host provider",
    ),
    debug: bool = typer.Option(False),
):
    """Create self host configuration file"""

    try:
        gen_provider_callbacks[provider]()
    except KeyError:
        typer.secho(
            f'Invalid provider {provider}. options are "", "gke"',
            fg=typer.colors.RED,
        )
    except Exception:
        typer.echo(f"unexpected error,")
        if debug:
            typer.secho(traceback.format_exc())
