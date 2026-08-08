"""Trigger a Robusta platform Triggered Workflow from an alert.

Fires the platform's ``POST /webhooks`` endpoint with the entire alert
payload (labels, annotations, status, timestamps, generatorURL, fingerprint)
plus the cluster name, so a Triggered Workflow — typically a Holmes
investigation — runs in response to the alert.

Example playbook configuration::

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: NodeCordonedManually
      actions:
      - trigger_workflow:
          workflow_id: "b7f9d2e4-1234-4c56-9abc-0123456789ab"
          api_key: "{{ env.ROBUSTA_PLATFORM_API_KEY }}"

Optionally, rate limit the action by alert label combination. Below, once a
workflow is triggered for an alert, further alerts matching on BOTH
``alertname`` and ``pod`` are skipped for ``rate_limit_seconds``
(default: 900)::

    customPlaybooks:
    - triggers:
      - on_prometheus_alert: {}
      actions:
      - trigger_workflow:
          workflow_id: "b7f9d2e4-1234-4c56-9abc-0123456789ab"
          api_key: "{{ env.ROBUSTA_PLATFORM_API_KEY }}"
          rate_limit_labels: ["alertname", "pod"]
          rate_limit_seconds: 3600
"""

import json
import logging
from typing import List, Optional, Union

import requests
from pydantic import SecretStr
from robusta.api import ActionException, ActionParams, ErrorCodes, PrometheusKubernetesAlert, RateLimiter, action


class TriggerWorkflowParams(ActionParams):
    """
    :var workflow_id: One or more Triggered Workflow ids to run. A single id,
        or a list to trigger several workflows from the same alert.
    :var api_key: Robusta platform account API key with ``alerts:WRITE``
        permission. Sent as ``Authorization: Bearer <key>``.
    :var url: The platform webhooks endpoint.
    :var account_id: (optional) Robusta account id. Defaults to the account
        this runner is connected to.
    :var origin: (optional) Origin label stored with the event, shown in the
        platform Delivery Log.
    :var route_to_alert_cluster: (optional) (Default: True) When True, the
        workflow runs against the cluster this alert fired in (via the
        ``cluster`` URL parameter), overriding the cluster configured on the
        workflow definition. Set False to always use the workflow's
        configured cluster.
    :var timeout: (optional) (Default: 30) Request timeout in seconds.
    :var rate_limit_labels: (optional) Alert labels to rate limit by, e.g.
        ``["alertname", "pod"]``. When set, alerts whose values match on ALL
        of these labels share one rate limit bucket: after the workflow is
        triggered once, further alerts with the same label combination are
        skipped (with a log) until ``rate_limit_seconds`` passes. By default
        no rate limit is applied.
    :var rate_limit_seconds: (optional) (Default: 900) The rate limit period,
        in seconds. Only relevant when ``rate_limit_labels`` is set.
    """

    workflow_id: Union[str, List[str]]
    api_key: SecretStr
    url: str = "https://api.robusta.dev/webhooks"
    account_id: Optional[str] = None
    origin: str = "robusta-runner"
    route_to_alert_cluster: bool = True
    timeout: int = 30
    rate_limit_labels: Optional[List[str]] = None
    rate_limit_seconds: int = 900


def build_workflow_trigger_payload(alert: PrometheusKubernetesAlert) -> dict:
    """The webhook body: the entire alert payload plus the cluster name.

    The alert is nested under ``alert`` untouched (labels, annotations,
    status, startsAt/endsAt, generatorURL, fingerprint), so workflow filters
    can match on any alert field; ``cluster_name`` rides alongside it.
    """
    context = alert.get_context()
    return {
        "cluster_name": context.cluster_name,
        "alert": json.loads(alert.alert.json()),
    }


def _rate_limit_allows(
    alert: PrometheusKubernetesAlert, params: TriggerWorkflowParams, workflow_ids: List[str]
) -> bool:
    """Mark this alert's rate limit bucket and return whether the action may run.

    Alerts share a bucket when they match on ALL of ``params.rate_limit_labels``
    (a label missing from the alert matches other alerts missing it too). The
    workflow ids are part of the bucket key, so separate trigger_workflow
    configurations don't rate limit each other.
    """
    label_values = ",".join(f"{label}={alert.alert.labels.get(label, '')}" for label in sorted(params.rate_limit_labels))
    limiter_id = f"{','.join(sorted(workflow_ids))}|{label_values}"
    if RateLimiter.mark_and_test("trigger_workflow", limiter_id, params.rate_limit_seconds):
        return True

    logging.info(
        f"trigger_workflow: rate limited for alert {alert.alert_name} ({label_values}); "
        f"skipping workflow(s) {workflow_ids} for {params.rate_limit_seconds} seconds since the last trigger"
    )
    return False


@action
def trigger_workflow(alert: PrometheusKubernetesAlert, params: TriggerWorkflowParams):
    """
    Trigger one or more Robusta platform Triggered Workflows (e.g. a Holmes
    investigation), sending the entire alert payload and the cluster name as
    the workflow's trigger payload.
    """
    workflow_ids = params.workflow_id if isinstance(params.workflow_id, list) else [params.workflow_id]
    workflow_ids = [w.strip() for w in workflow_ids if w and w.strip()]
    if not workflow_ids:
        raise ActionException(ErrorCodes.ACTION_UNEXPECTED_ERROR, "trigger_workflow: no workflow_id provided")

    if params.rate_limit_labels and not _rate_limit_allows(alert, params, workflow_ids):
        return

    context = alert.get_context()
    account_id = params.account_id or context.account_id

    query_params: List[tuple] = [("account_id", account_id), ("origin", params.origin)]
    query_params.extend(("workflow_id", workflow_id) for workflow_id in workflow_ids)
    if params.route_to_alert_cluster:
        query_params.append(("cluster", context.cluster_name))

    payload = build_workflow_trigger_payload(alert)

    try:
        response = requests.post(
            params.url,
            params=query_params,
            json=payload,
            headers={"Authorization": f"Bearer {params.api_key.get_secret_value()}"},
            timeout=params.timeout,
        )
    except Exception as e:
        raise ActionException(
            ErrorCodes.ACTION_UNEXPECTED_ERROR,
            f"trigger_workflow: failed to reach {params.url} for alert {alert.alert_name}: {e}",
        )

    if not (200 <= response.status_code < 300):
        raise ActionException(
            ErrorCodes.ACTION_UNEXPECTED_ERROR,
            f"trigger_workflow: {params.url} returned {response.status_code} "
            f"for alert {alert.alert_name}: {response.text[:500]}",
        )

    logging.info(
        f"trigger_workflow: triggered workflow(s) {workflow_ids} for alert "
        f"{alert.alert_name} on cluster {context.cluster_name}"
    )
