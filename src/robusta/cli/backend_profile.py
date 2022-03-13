import json
import os
import sys

import typer

ROBUSTA_BACKEND_PROFILE = os.environ.get("ROBUSTA_BACKEND_PROFILE", "")


class BackendProfile:
    def __init__(self):
        self.robusta_cloud_api_host = "https://api.robusta.dev"
        self.robusta_ui_domain = "https://platform.robusta.dev"
        self.custom_profile = False
        if ROBUSTA_BACKEND_PROFILE:
            typer.secho(
                f"Using Robusta backend profile: {ROBUSTA_BACKEND_PROFILE}",
                color="blue",
            )
            with open(ROBUSTA_BACKEND_PROFILE, "r") as profile:
                json_content = json.load(profile)
                for attribute in [
                    "ROBUSTA_CLOUD_API_HOST",
                    "ROBUTA_UI_DOMAIN",
                    "ROBUSTA_RELAY_WS_ADDR",
                    "RELAY_EXTERNAL_ACTIONS_URL",
                ]:
                    if not json_content.get(attribute, None):
                        typer.secho(f"Illegal profile. Missing {attribute}. Aborting!")
                        sys.exit(1)

                self.robusta_cloud_api_host = json_content.get("ROBUSTA_CLOUD_API_HOST")
                self.robusta_ui_domain = json_content.get("ROBUTA_UI_DOMAIN")
                self.robusta_relay_ws_address = json_content.get(
                    "ROBUSTA_RELAY_WS_ADDR"
                )
                self.robusta_relay_external_actions_url = json_content.get(
                    "RELAY_EXTERNAL_ACTIONS_URL"
                )
                self.custom_profile = True


backend_profile = BackendProfile()
