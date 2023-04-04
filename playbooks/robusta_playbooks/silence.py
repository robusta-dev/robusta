import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

import requests
from pydantic import BaseModel, SecretStr, validator

from robusta.api import (
    ActionException,
    ActionParams,
    AlertManagerDiscovery,
    ErrorCodes,
    ExecutionBaseEvent,
    MarkdownBlock,
    ServiceDiscovery,
    TableBlock,
    action,
)

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


class BaseSilenceParams(ActionParams):
    """
    :var alertmanager_url: Alternative Alert Manager url to send requests.
    """

    alertmanager_flavor: str = None  # type: ignore
    alertmanager_url: Optional[str]
    alertmanager_auth: Optional[SecretStr] = None
    grafana_api_key: str = None  # type: ignore

    @validator("alertmanager_url", allow_reuse=True)
    def remove_ending_slash(cls, v):
        if v.endswith("/"):
            return v[:-1]
        return v


class DeleteSilenceParams(BaseSilenceParams):
    """
    :var id: uuid of the silence.
    """

    id: str


class AddSilenceParams(BaseSilenceParams):
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


@action
def get_silences(event: ExecutionBaseEvent, params: BaseSilenceParams):
    alertmanager_url = _get_alertmanager_url(params)
    if not alertmanager_url:
        raise ActionException(ErrorCodes.ALERT_MANAGER_DISCOVERY_FAILED)

    try:
        response = requests.get(
            f"{alertmanager_url}{_get_url_path(SilenceOperation.LIST, params)}",
            headers=_gen_headers(params),
        )
    except Exception as e:
        logging.error(f"Failed to get alertmanager silences. url: {alertmanager_url} {e}", exc_info=True)
        raise ActionException(ErrorCodes.ALERT_MANAGER_REQUEST_FAILED) from e

    silence_list = [(Silence(**silence).to_list()) for silence in response.json()]
    if len(silence_list) == 0:
        event.add_enrichment([MarkdownBlock("*There are no silences*")])
        return

    event.add_enrichment(
        [
            TableBlock(
                rows=silence_list,
                headers=[*Silence.__fields__],
                table_name="Silences",
            ),
        ]
    )


@action
def add_silence(event: ExecutionBaseEvent, params: AddSilenceParams):
    alertmanager_url = _get_alertmanager_url(params)
    if not alertmanager_url:
        raise ActionException(ErrorCodes.ALERT_MANAGER_DISCOVERY_FAILED)

    try:
        res = requests.post(
            f"{alertmanager_url}{_get_url_path(SilenceOperation.CREATE, params)}",
            data=params.json(exclude_defaults=True),  # support old versions.
            headers=_gen_headers(params),
        )
    except Exception as e:
        logging.error(f"Failed to add silence to alertmanager. url: {alertmanager_url} {e}", exc_info=True)
        raise ActionException(ErrorCodes.ALERT_MANAGER_REQUEST_FAILED) from e

    if not res.ok:
        raise ActionException(ErrorCodes.ADD_SILENCE_FAILED, msg=f"Add silence failed: {res.text}")

    silence_id = res.json().get("silenceID") or res.json().get("id")  # on grafana alertmanager the 'id' is returned
    if not silence_id:
        raise ActionException(ErrorCodes.ADD_SILENCE_FAILED)

    event.add_enrichment(
        [
            TableBlock(
                rows=[[silence_id]],
                headers=["id"],
                table_name="New Silence",
            ),
        ]
    )


@action
def delete_silence(event: ExecutionBaseEvent, params: DeleteSilenceParams):
    alertmanager_url = _get_alertmanager_url(params)
    if not alertmanager_url:
        raise ActionException(ErrorCodes.ALERT_MANAGER_DISCOVERY_FAILED)

    try:
        alertmanager_url = _get_alertmanager_url(params)

        requests.delete(
            f"{alertmanager_url}{_get_url_path(SilenceOperation.DELETE, params)}/{params.id}",
            headers=_gen_headers(params),
        )
    except Exception as e:
        logging.error(f"Failed to delete alertmanager silence. url: {alertmanager_url} {e}", exc_info=True)
        raise ActionException(ErrorCodes.ALERT_MANAGER_REQUEST_FAILED) from e

    event.add_enrichment(
        [
            TableBlock(
                rows=[[params.id]],
                headers=["id"],
                table_name="Deleted Silence",
            ),
        ]
    )


SilenceOperation = Enum("SilenceOperation", "CREATE DELETE LIST")


def _gen_headers(params: BaseSilenceParams) -> Dict:
    headers = {"Content-type": "application/json"}

    if params.grafana_api_key:
        headers.update({"Authorization": f"Bearer {params.grafana_api_key}"})

    elif params.alertmanager_auth:
        headers.update({"Authorization": params.alertmanager_auth.get_secret_value()})

    return headers


def _get_url_path(operation: SilenceOperation, params: BaseSilenceParams) -> str:
    prefix = ""
    if "grafana" == params.alertmanager_flavor:
        prefix = "/api/alertmanager/grafana"

    if operation == SilenceOperation.DELETE:
        return f"{prefix}/api/v2/silence"
    else:
        return f"{prefix}/api/v2/silences"


def _get_alertmanager_url(params: BaseSilenceParams) -> str:
    if params.alertmanager_url:
        return params.alertmanager_url

    if "grafana" == params.alertmanager_flavor:
        return ServiceDiscovery.find_url(
            selectors=["app.kubernetes.io/name=grafana"], error_msg="Failed to find grafana url"
        )

    return AlertManagerDiscovery.find_alert_manager_url()
