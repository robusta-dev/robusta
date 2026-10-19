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

``trigger_workflow_event`` does the same for any other trigger. Below, a
workflow runs each time a Deployment rollout in ``payments`` completes::

    customPlaybooks:
    - triggers:
      - on_deployment_rollout_complete:
          namespace_prefix: payments
      actions:
      - trigger_workflow_event:
          workflow_id: "b7f9d2e4-1234-4c56-9abc-0123456789ab"
          api_key: "{{ env.ROBUSTA_PLATFORM_API_KEY }}"
"""

import json
import logging
from typing import Any, List, Optional, Union

import requests
from hikaru import HikaruBase
from pydantic.v1 import SecretStr
from robusta.api import (
    ActionException,
    ActionParams,
    ErrorCodes,
    ExecutionBaseEvent,
    FindingSubject,
    KubernetesAnyChangeEvent,
    PrometheusKubernetesAlert,
    RateLimiter,
    action,
)
from robusta.core.model.events import ExecutionContext


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


def _workflow_ids(params: Union["TriggerWorkflowParams", "TriggerWorkflowEventParams"], action_name: str) -> List[str]:
    workflow_ids = params.workflow_id if isinstance(params.workflow_id, list) else [params.workflow_id]
    workflow_ids = [w.strip() for w in workflow_ids if w and w.strip()]
    if not workflow_ids:
        raise ActionException(ErrorCodes.ACTION_UNEXPECTED_ERROR, f"{action_name}: no workflow_id provided")
    return workflow_ids


def _post_workflow_trigger(
    params: Union["TriggerWorkflowParams", "TriggerWorkflowEventParams"],
    action_name: str,
    context: ExecutionContext,
    workflow_ids: List[str],
    cluster: Optional[str],
    event_type: Optional[str],
    payload: dict,
    event_desc: str,
):
    query_params: List[tuple] = [("account_id", params.account_id or context.account_id), ("origin", params.origin)]
    query_params.extend(("workflow_id", workflow_id) for workflow_id in workflow_ids)
    if cluster is not None:
        query_params.append(("cluster", cluster))
    if event_type:
        query_params.append(("type", event_type))

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
            f"{action_name}: failed to reach {params.url} for {event_desc}: {e}",
        )

    if not (200 <= response.status_code < 300):
        raise ActionException(
            ErrorCodes.ACTION_UNEXPECTED_ERROR,
            f"{action_name}: {params.url} returned {response.status_code} for {event_desc}: {response.text[:500]}",
        )

    logging.info(
        f"{action_name}: triggered workflow(s) {workflow_ids} for {event_desc} on cluster {context.cluster_name}"
    )


@action
def trigger_workflow(alert: PrometheusKubernetesAlert, params: TriggerWorkflowParams):
    """
    Trigger one or more Robusta platform Triggered Workflows (e.g. a Holmes
    investigation), sending the entire alert payload and the cluster name as
    the workflow's trigger payload.
    """
    workflow_ids = _workflow_ids(params, "trigger_workflow")

    if params.rate_limit_labels and not _rate_limit_allows(alert, params, workflow_ids):
        return

    context = alert.get_context()
    _post_workflow_trigger(
        params,
        "trigger_workflow",
        context,
        workflow_ids,
        cluster=context.cluster_name if params.route_to_alert_cluster else None,
        event_type=None,
        payload=build_workflow_trigger_payload(alert),
        event_desc=f"alert {alert.alert_name}",
    )


class TriggerWorkflowEventParams(ActionParams):
    """
    :var workflow_id: One or more Triggered Workflow ids to run. A single id,
        or a list to trigger several workflows from the same event.
    :var api_key: Robusta platform account API key with ``alerts:WRITE``
        permission. Sent as ``Authorization: Bearer <key>``.
    :var url: The platform webhooks endpoint.
    :var account_id: (optional) Robusta account id. Defaults to the account
        this runner is connected to.
    :var origin: (optional) Origin label stored with the event, shown in the
        platform Delivery Log.
    :var route_to_event_cluster: (optional) (Default: True) When True, the
        workflow runs against the cluster the event came from (via the
        ``cluster`` URL parameter), overriding the cluster configured on the
        workflow definition. Set False to always use the workflow's
        configured cluster.
    :var timeout: (optional) (Default: 30) Request timeout in seconds.
    :var rate_limit_seconds: (optional) When set, the workflow is triggered at
        most once per period for the same event on the same subject (kind,
        namespace and name, e.g. one Deployment); further events are skipped
        with a log. A completed and a failed rollout of one Deployment are
        limited separately. Events whose subject can't be resolved (e.g.
        scheduled triggers) share one limit. By default no rate limit is applied.
    """

    workflow_id: Union[str, List[str]]
    api_key: SecretStr
    url: str = "https://api.robusta.dev/webhooks"
    account_id: Optional[str] = None
    origin: str = "robusta-runner"
    route_to_event_cluster: bool = True
    timeout: int = 30
    rate_limit_seconds: Optional[int] = None


# Duplicates the whole object in every manifest applied with `kubectl apply`.
LAST_APPLIED_ANNOTATION = "kubectl.kubernetes.io/last-applied-configuration"


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, HikaruBase):
        return value.to_dict()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return str(value)


SECRET_VALUE_FIELDS = ("data", "stringData")
REDACTED = "<redacted>"


def _is_secret(obj: Any) -> bool:
    return getattr(obj, "kind", None) == "Secret"


def _resource_manifest(obj: HikaruBase) -> dict:
    manifest = obj.to_dict()
    metadata = manifest.get("metadata") or {}
    metadata.pop("managedFields", None)
    annotations = metadata.get("annotations") or {}
    annotations.pop(LAST_APPLIED_ANNOTATION, None)
    if _is_secret(obj):
        for field in SECRET_VALUE_FIELDS:
            if manifest.get(field):
                manifest[field] = {key: REDACTED for key in manifest[field]}
    return manifest


def _subject_kind(event: ExecutionBaseEvent, subject: FindingSubject) -> Optional[str]:
    # FindingSubjectType only names a few kinds; anything else (Secret, Service, Ingress, ...) is TYPE_NONE
    kind = subject.subject_type.value or getattr(getattr(event, "obj", None), "kind", None)
    return kind.lower() if kind else None


def _diff_path(path: List[Union[str, int]]) -> str:
    """``["spec", "containers", 0, "image"]`` -> ``spec.containers[0].image``"""
    formatted = ""
    for part in path:
        formatted += f"[{part}]" if isinstance(part, int) else f".{part}"
    return formatted.lstrip(".")


def _event_type(event: ExecutionBaseEvent) -> str:
    """The platform event type, shown in the Delivery Log."""
    if isinstance(event, PrometheusKubernetesAlert):
        return "alert"
    if isinstance(event, KubernetesAnyChangeEvent) and getattr(event.obj, "kind", None) != "Event":
        return "change"
    return "event"


def build_event_workflow_payload(event: ExecutionBaseEvent) -> dict:
    """The webhook body for any trigger: what the event is about, plus whatever the event carries.

    ``alert`` is the full Prometheus alert, ``operation``/``diff`` describe a Kubernetes change (``diff``
    is present only when the trigger sets change_filters, and holds the diffs they kept), and
    ``resource`` is the current manifest of the Kubernetes object the event is about. Secret values
    are redacted.
    """
    subject = event.get_subject()
    body = {
        "trigger": type(event).__name__,
        "subject": {
            "kind": _subject_kind(event, subject),
            "name": subject.name,
            "namespace": subject.namespace,
            "node": subject.node,
            "labels": subject.labels,
        },
    }

    if isinstance(event, PrometheusKubernetesAlert) and event.alert:
        body["alert"] = json.loads(event.alert.json())

    if isinstance(event, KubernetesAnyChangeEvent):
        if event.operation:
            body["operation"] = event.operation.value
        if event.description:
            body["description"] = event.description
        if event.filtered_diffs:
            redact = _is_secret(event.obj)
            body["diff"] = [
                {
                    "path": _diff_path(diff.path),
                    "type": diff.diff_type.name.lower(),
                    "old": REDACTED if redact else _to_jsonable(diff.other_value),
                    "new": REDACTED if redact else _to_jsonable(diff.value),
                }
                for diff in event.filtered_diffs
            ]

    if isinstance(event, PrometheusKubernetesAlert):
        obj = event.get_resource()
    else:
        obj = getattr(event, "obj", None)
    if isinstance(obj, HikaruBase):
        body["resource"] = _resource_manifest(obj)

    return {"cluster_name": event.get_context().cluster_name, "event": body}


def _subject_rate_limit_allows(
    event: ExecutionBaseEvent, params: TriggerWorkflowEventParams, workflow_ids: List[str]
) -> bool:
    subject = event.get_subject()
    subject_key = f"{_subject_kind(event, subject)}/{subject.namespace or ''}/{subject.name or ''}"
    # The description tells apart different events on one subject, e.g. a rollout that failed and then completed
    limiter_id = f"{','.join(sorted(workflow_ids))}|{subject_key}|{getattr(event, 'description', '')}"
    if RateLimiter.mark_and_test("trigger_workflow_event", limiter_id, params.rate_limit_seconds):
        return True

    logging.info(
        f"trigger_workflow_event: rate limited for {subject_key}; skipping workflow(s) {workflow_ids} "
        f"for {params.rate_limit_seconds} seconds since the last trigger"
    )
    return False


@action
def trigger_workflow_event(event: ExecutionBaseEvent, params: TriggerWorkflowEventParams):
    """
    Trigger one or more Robusta platform Triggered Workflows (e.g. a Holmes
    investigation) from any trigger, such as a Kubernetes change, a completed
    or failed Deployment rollout, a failed Job or a Prometheus alert. Sends the
    event's subject, the change diff, the alert and the current Kubernetes
    manifest (whichever the event has) together with the cluster name as the
    workflow's trigger payload.
    """
    workflow_ids = _workflow_ids(params, "trigger_workflow_event")

    if params.rate_limit_seconds and not _subject_rate_limit_allows(event, params, workflow_ids):
        return

    context = event.get_context()
    _post_workflow_trigger(
        params,
        "trigger_workflow_event",
        context,
        workflow_ids,
        cluster=context.cluster_name if params.route_to_event_cluster else None,
        event_type=_event_type(event),
        payload=build_event_workflow_payload(event),
        event_desc=f"{type(event).__name__} {event.get_subject()}",
    )
