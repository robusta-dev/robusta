import logging
from typing import Optional

from robusta.api import (
    ActionException,
    ActionParams,
    ErrorCodes,
    PodEvent,
    PrometheusKubernetesAlert,
    RateLimiter,
    action,
)


@action
def delete_pod(event: PodEvent):
    """
    Deletes a pod
    """
    if not event.get_pod():
        raise ActionException(ErrorCodes.RESOURCE_NOT_FOUND, "Failed to get the pod for deletion")

    event.get_pod().delete()


class DeleteAlertPodParams(ActionParams):
    """
    :var rate_limit: Optional rate limit (seconds). If set, the action will only run once per period for the same alert label value.
    :var rate_limit_field: Alert label name whose value is used to build the rate limit key.
    """

    rate_limit: Optional[int] = None
    rate_limit_field: Optional[str] = None


@action
def delete_alert_pod(event: PrometheusKubernetesAlert, params: DeleteAlertPodParams):
    """
    Deletes the pod associated with a Prometheus alert.

    Supports an optional rate limit, scoped by an alert label value.
    """
    pod = event.get_pod()
    if not pod:
        raise ActionException(ErrorCodes.RESOURCE_NOT_FOUND, "Failed to get the pod for deletion")

    if params.rate_limit is not None:
        if not params.rate_limit_field:
            raise ActionException(
                ErrorCodes.ILLEGAL_ACTION_PARAMS,
                "rate_limit_field must be set when rate_limit is configured",
            )

        field_value = event.alert.labels.get(params.rate_limit_field)
        if field_value is None:
            logging.warning(
                f"delete_alert_pod: alert missing label '{params.rate_limit_field}'; skipping rate limit check"
            )
        else:
            key = f"{params.rate_limit_field}:{field_value}"
            if not RateLimiter.mark_and_test("delete_alert_pod", key, params.rate_limit):
                logging.info(f"delete_alert_pod rate limited for {key}; skipping deletion")
                return

    pod.delete()
