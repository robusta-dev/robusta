import json
import os
import sys

import typer
from pydantic.main import BaseModel

ROBUSTA_BACKEND_PROFILE = os.environ.get("ROBUSTA_BACKEND_PROFILE", "")


class BackendProfile(BaseModel):
    robusta_cloud_api_host: str = ""
    robusta_ui_domain: str = ""
    robusta_relay_ws_address: str = ""
    robusta_relay_external_actions_url: str = ""
    robusta_telemetry_endpoint: str = ""
    robusta_store_token_url: str = ""
    custom_profile: bool = False

    @classmethod
    def fromDomain(cls, domain: str):
        return cls(
            robusta_cloud_api_host=f"https://api.{domain}",
            robusta_ui_domain=f"https://platform.{domain}",
            robusta_relay_ws_address=f"wss://relay.{domain}",
            robusta_relay_external_actions_url=f"https://api.{domain}/integrations/generic/actions",
            robusta_telemetry_endpoint=f"https://api.{domain}/telemetry",
            robusta_store_token_url=f"https://api.{domain}/auth/server/tokens",
        )


# default values
backend_profile = BackendProfile(
    robusta_cloud_api_host="https://api.robusta.dev",
    robusta_ui_domain="https://platform.robusta.dev",
    robusta_store_token_url="https://api.robusta.dev/auth/server/tokens",
)

if ROBUSTA_BACKEND_PROFILE:
    typer.secho(
        f"Using Robusta backend profile: {ROBUSTA_BACKEND_PROFILE}",
        color="blue",
    )
    backend_profile = BackendProfile.parse_file(ROBUSTA_BACKEND_PROFILE)
    backend_profile.custom_profile = True

    profile_dict = backend_profile.dict()
    for attribute, val in profile_dict.items():
        if not profile_dict.get(attribute):
            typer.secho(f"Illegal profile. Missing {attribute}. Aborting!")
            sys.exit(1)
