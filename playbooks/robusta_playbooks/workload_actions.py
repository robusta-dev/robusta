import datetime
import logging

import pytz

from robusta.api import (
    ActionException,
    ErrorCodes,
    ExecutionBaseEvent,
    KubernetesResourceEvent,
    MarkdownBlock,
    NamespacedResourcesParams,
    action,
)
from robusta.integrations.kubernetes.custom_models import Rollout

ROLLOUT_RESTART_DEPRECATED = "rollout_restart is deprecated and no longer supported"


@action
def restart_named_rollout(event: ExecutionBaseEvent, params: NamespacedResourcesParams):
    """
    Performs rollout restart on a named argo rollout.
    """
    rollout = Rollout.readNamespaced(params.name, params.namespace).obj
    if not rollout:
        logging.info(f"Rollout {params.namespace}/{params.name} not found. Skipping restart_named_rollout")
        return

    now: str = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
    rollout.spec.restartAt = now
    rollout.update()

    event.add_enrichment([MarkdownBlock(f"rollout/{params.namespace}/{params.name} restarted")])


@action
def rollout_restart(event: KubernetesResourceEvent):
    """
    Deprecated. This action is no longer supported and returns an error.
    """
    logging.error(ROLLOUT_RESTART_DEPRECATED)
    raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, ROLLOUT_RESTART_DEPRECATED)
