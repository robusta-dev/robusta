import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

import requests
from pydantic import BaseModel, SecretStr, validator

from robusta.core.exceptions import AlertsManagerNotFound, NoAlertManagerUrlFound
from robusta.core.model.base_params import ActionParams
from robusta.integrations import openshift
from robusta.integrations.prometheus.utils import AlertManagerDiscovery, ServiceDiscovery

# ref to api https://github.com/prometheus/alertmanager/blob/main/api/v2/openapi.yaml


class Matcher(BaseModel):
    # https://github.com/prometheus/alertmanager/blob/main/api/v2/models/matcher.go
    isEqual: bool = (
        True  # support old version matchers with omitted isEqual https://github.com/prometheus/alertmanager/pull/2603
    )
    isRegex: bool
    name: str
    value: str


class SilenceStatus(BaseModel):
    # https://github.com/prometheus/alertmanager/blob/main/api/v2/models/silence_status.go
    state: str


class Silence(BaseModel):
    # https://github.com/prometheus/alertmanager/blob/main/api/v2/models/silence.go
    id: UUID
    status: SilenceStatus
    comment: str
    createdBy: str
    startsAt: datetime
    endsAt: datetime
    matchers: List[Matcher]

    def to_list(self) -> List[str]:
        return [
            str(self.id),
            self.status.json(),
            self.comment,
            self.createdBy,
            self.startsAt.isoformat(timespec="seconds"),
            self.endsAt.isoformat(timespec="seconds"),
            json.dumps([matcher.dict() for matcher in self.matchers]),
        ]


class AlertManagerParams(ActionParams):
    """
    :var alertmanager_url: Alternative Alert Manager url to send requests.
    """

    alertmanager_flavor: str = None  # type: ignore
    alertmanager_url: Optional[str]
    alertmanager_auth: Optional[SecretStr] = None
    grafana_api_key: str = None  # type: ignore

    @validator("alertmanager_url", allow_reuse=True)
    def validate_alertmanager_url(cls, v):

        if v and not v.startswith("http"):  # if the user configured url without http(s)
            v = f"http://{v}"
            logging.info(f"Adding protocol to alertmanager_url: {v}")

        if v.endswith("/"):
            return v[:-1]
        return v

    @validator("alertmanager_auth", allow_reuse=True, always=True)
    def auto_openshift_token(cls, v: Optional[SecretStr]):
        # If openshift is enabled, and the user didn't configure alertmanager_auth, we will try to load the token from the service account
        if v is not None:
            return v

        openshift_token = openshift.load_token()
        if openshift_token is not None:
            logging.debug(f"Using openshift token from {openshift.TOKEN_LOCATION} for alertmanager auth")
            return SecretStr(f"Bearer {openshift_token}")

        return None


class DeleteSilenceParams(AlertManagerParams):
    """
    :var id: uuid of the silence.
    """

    id: str


class AddSilenceParams(AlertManagerParams):
    """
    :var id: uuid of the silence. use for update, empty on create.
    :var comment: text comment of the silence.
    :var createdBy: author of the silence.
    :var startsAt: date.
    :var endsAt: date.
    :var matchers: List of matchers to filter the silence effect.
    """

    id: Optional[str]
    comment: str
    createdBy: str
    startsAt: datetime
    endsAt: datetime
    matchers: List[Matcher]


def get_alertmanager_silences_connection(params: AlertManagerParams):
    alertmanager_url = get_alertmanager_url(params)

    if not alertmanager_url:
        raise NoAlertManagerUrlFound("AlertManager url could not be found. Add 'alertmanager_url' under global_config")
    try:
        response = requests.get(
            f"{alertmanager_url}{get_alertmanager_url_path(SilenceOperation.LIST, params)}",
            headers=gen_alertmanager_headers(params),
        )
        response.raise_for_status()

    except Exception as e:
        raise AlertsManagerNotFound(
            f"Could not connect to the alert manager [{alertmanager_url}] \nCaused by {e.__class__.__name__}: {e})"
        ) from e


SilenceOperation = Enum("SilenceOperation", "CREATE DELETE LIST")


def gen_alertmanager_headers(params: AlertManagerParams) -> Dict:
    headers = {"Content-type": "application/json"}

    if params.grafana_api_key:
        headers.update({"Authorization": f"Bearer {params.grafana_api_key}"})

    elif params.alertmanager_auth:
        headers.update({"Authorization": params.alertmanager_auth.get_secret_value()})

    return headers


def get_alertmanager_url_path(operation: SilenceOperation, params: AlertManagerParams) -> str:
    prefix = ""
    if "grafana" == params.alertmanager_flavor:
        prefix = "/api/alertmanager/grafana"

    if operation == SilenceOperation.DELETE:
        return f"{prefix}/api/v2/silence"
    else:
        return f"{prefix}/api/v2/silences"


def get_alertmanager_url(params: AlertManagerParams) -> str:
    if params.alertmanager_url:
        return params.alertmanager_url

    if "grafana" == params.alertmanager_flavor:
        return ServiceDiscovery.find_url(
            selectors=["app.kubernetes.io/name=grafana"], error_msg="Failed to find grafana url"
        )

    return AlertManagerDiscovery.find_alert_manager_url()
