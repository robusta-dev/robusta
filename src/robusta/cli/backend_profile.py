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


# default values
backend_profile = BackendProfile(
    robusta_cloud_api_host="https://api.robusta.dev",
    robusta_ui_domain="https://platform.robusta.dev",
    robusta_store_token_url="https://api.robusta.dev/auth/server/tokens"
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
