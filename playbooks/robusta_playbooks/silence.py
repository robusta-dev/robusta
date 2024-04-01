import logging

import requests

from robusta.api import (
    ActionException,
    ErrorCodes,
    ExecutionBaseEvent,
    MarkdownBlock,
    TableBlock,
    action,
    get_alertmanager_url,
    AlertManagerParams,
    get_alertmanager_url_path,
    SilenceOperation,
    gen_alertmanager_headers,
    Silence,
    AddSilenceParams,
    DeleteSilenceParams
)


@action
def get_silences(event: ExecutionBaseEvent, params: AlertManagerParams):
    alertmanager_url = get_alertmanager_url(params)
    if not alertmanager_url:
        raise ActionException(ErrorCodes.ALERT_MANAGER_DISCOVERY_FAILED)

    try:
        response = requests.get(
            f"{alertmanager_url}{get_alertmanager_url_path(SilenceOperation.LIST, params)}",
            headers=gen_alertmanager_headers(params),
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
    alertmanager_url = get_alertmanager_url(params)
    if not alertmanager_url:
        raise ActionException(ErrorCodes.ALERT_MANAGER_DISCOVERY_FAILED)

    try:
        res = requests.post(
            f"{alertmanager_url}{get_alertmanager_url_path(SilenceOperation.CREATE, params)}",
            data=params.json(exclude_defaults=True),  # support old versions.
            headers=gen_alertmanager_headers(params),
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
    alertmanager_url = get_alertmanager_url(params)
    if not alertmanager_url:
        raise ActionException(ErrorCodes.ALERT_MANAGER_DISCOVERY_FAILED)

    try:
        alertmanager_url = get_alertmanager_url(params)

        requests.delete(
            f"{alertmanager_url}{get_alertmanager_url_path(SilenceOperation.DELETE, params)}/{params.id}",
            headers=gen_alertmanager_headers(params),
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
