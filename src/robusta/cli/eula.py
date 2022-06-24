import requests
import typer
from .backend_profile import backend_profile


def handle_eula(account_id, robusta_api_key, cloud_routing_enabled):
    require_eula = robusta_api_key or cloud_routing_enabled
    if not require_eula:
        return

    while True:
        eula_url = f"{backend_profile.robusta_cloud_api_host}/eula.html"
        typer.echo(
            f"Please read and approve our End User License Agreement: {eula_url}"
        )
        eula_approved = typer.confirm("Do you accept our End User License Agreement?")

        if eula_approved:
            try:
                requests.get(f"{eula_url}?account_id={account_id}")
            except Exception:
                typer.echo(f"\nEula approval failed: {eula_url}")
            return

        typer.secho(
            "End User License Agreement rejected. Sorry, you must either accept or restart the installation and disable the UI and cloud features",
            fg="red",
        )
