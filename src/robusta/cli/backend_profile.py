import os
import sys

import typer
from pydantic.main import BaseModel

from robusta.cli.utils import host_for_params

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
    def fromDomainProvider(
        cls, domain: str, api_endpoint_prefix: str, platform_endpoint_prefix: str, relay_endpoint_prefix: str
    ):
        return cls(
            robusta_cloud_api_host=host_for_params(api_endpoint_prefix, domain),
            robusta_ui_domain=host_for_params(platform_endpoint_prefix, domain),
            robusta_relay_ws_address=host_for_params(relay_endpoint_prefix, domain, "wss"),
            robusta_relay_external_actions_url=f"{host_for_params(api_endpoint_prefix, domain)}/integrations/generic/actions",
            robusta_telemetry_endpoint=f"{host_for_params(api_endpoint_prefix, domain)}/telemetry",
            robusta_store_token_url=f"{host_for_params(api_endpoint_prefix, domain)}/auth/server/tokens",
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
