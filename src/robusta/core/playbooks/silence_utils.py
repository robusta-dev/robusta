import datetime
import logging
from enum import Enum
from typing import Dict, Optional

import requests

from robusta.core.model.base_params import AddSilenceParams, BaseSilenceParams, SilenceMatcher
from robusta.core.model.env_vars import AUTO_SILENCE_ALERTS
from robusta.integrations.prometheus.models import PrometheusKubernetesAlert
from robusta.integrations.prometheus.utils import AlertManagerDiscovery, ServiceDiscovery
from robusta.utils.error_codes import ActionException, ErrorCodes

SilenceOperation = Enum("SilenceOperation", "CREATE DELETE LIST")


def create_label_matcher(name: str, value: str, isRegex: bool) -> SilenceMatcher:
    return SilenceMatcher(name=name, value=value, isEqual=not isRegex, isRegex=isRegex)


def add_silence_from_prometheus_alert(alert: PrometheusKubernetesAlert, labels: [str], comment: Optional[str] = None,
                                      log_message: Optional[str] = None):
    if not AUTO_SILENCE_ALERTS:
        return
    logging.info(log_message)
    matchers = [create_label_matcher(name=label, value=alert.get_alert_label(label), isRegex=False)
                for label in labels if alert.get_alert_label(label)]
    if not comment:
        comment = "This alert was auto-silenced"
    created_by = "robusta auto-silencer"
    starts_at = datetime.datetime.now()
    ends_at = datetime.datetime.now() + datetime.timedelta(weeks=52 * 5)  # silence for 5 years
    silence_params = AddSilenceParams(matchers=matchers, comment=comment, createdBy=created_by, startsAt=starts_at,
                                      endsAt=ends_at)
    add_silence_to_alert_manager(silence_params)


def add_silence_to_alert_manager(params: AddSilenceParams):
    alertmanager_url = silence_get_alertmanager_url(params)
    if not alertmanager_url:
        raise ActionException(ErrorCodes.ALERT_MANAGER_DISCOVERY_FAILED)

    try:
        res = requests.post(
            f"{alertmanager_url}{silence_get_url_path(SilenceOperation.CREATE, params)}",
            data=params.json(exclude_defaults=True),  # support old versions.
            headers=silence_gen_headers(params),
        )
    except Exception as e:
        raise ActionException(ErrorCodes.ALERT_MANAGER_REQUEST_FAILED) from e

    if not res.ok:
        raise ActionException(ErrorCodes.ADD_SILENCE_FAILED, msg=f"Add silence failed: {res.text}")

    silence_id = res.json().get("silenceID") or res.json().get("id")  # on grafana alertmanager the 'id' is returned
    if not silence_id:
        raise ActionException(ErrorCodes.ADD_SILENCE_FAILED)
    return silence_id


def silence_gen_headers(params: BaseSilenceParams) -> Dict:
    headers = {"Content-type": "application/json"}
    if params.grafana_api_key:
        headers.update({"Authorization": "Bearer {0}".format(params.grafana_api_key)})
    return headers


def silence_get_url_path(operation: SilenceOperation, params: BaseSilenceParams) -> str:
    prefix = ""
    if "grafana" == params.alertmanager_flavor:
        prefix = "/api/alertmanager/grafana"

    if operation == SilenceOperation.DELETE:
        return f"{prefix}/api/v2/silence"
    else:
        return f"{prefix}/api/v2/silences"


def silence_get_alertmanager_url(params: BaseSilenceParams) -> str:
    if params.alertmanager_url:
        return params.alertmanager_url

    if "grafana" == params.alertmanager_flavor:
        return ServiceDiscovery.find_url(
            selectors=["app.kubernetes.io/name=grafana"], error_msg="Failed to find grafana url"
        )

    return AlertManagerDiscovery.find_alert_manager_url()
