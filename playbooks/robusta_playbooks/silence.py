import json
from datetime import datetime
from typing import List
from uuid import UUID

import requests
from pydantic import BaseModel
from robusta.api import (
    ActionException,
    AddSilenceParams,
    BaseSilenceParams,
    DeleteSilenceParams,
    ErrorCodes,
    ExecutionBaseEvent,
    MarkdownBlock,
    SilenceMatcher,
    SilenceOperation,
    TableBlock,
    action,
    add_silence_to_alert_manager,
    silence_gen_headers,
    silence_get_alertmanager_url,
    silence_get_url_path,
)

# ref to api https://github.com/prometheus/alertmanager/blob/main/api/v2/openapi.yaml


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
    matchers: List[SilenceMatcher]

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


@action
def get_silences(event: ExecutionBaseEvent, params: BaseSilenceParams):
    alertmanager_url = silence_get_alertmanager_url(params)
    if not alertmanager_url:
        raise ActionException(ErrorCodes.ALERT_MANAGER_DISCOVERY_FAILED)

    try:
        response = requests.get(
            f"{alertmanager_url}{silence_get_url_path(SilenceOperation.LIST, params)}",
            headers=silence_gen_headers(params),
        )
    except Exception as e:
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
    silence_id = add_silence_to_alert_manager(params)
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
    alertmanager_url = silence_get_alertmanager_url(params)
    if not alertmanager_url:
        raise ActionException(ErrorCodes.ALERT_MANAGER_DISCOVERY_FAILED)

    try:
        alertmanager_url = silence_get_alertmanager_url(params)

        requests.delete(
            f"{alertmanager_url}{silence_get_url_path(SilenceOperation.DELETE, params)}/{params.id}",
            headers=silence_gen_headers(params),
        )
    except Exception as e:
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


