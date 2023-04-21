import re
from typing import List

import hikaru
from hikaru.meta import HikaruBase
from pydantic import SecretStr

from robusta.api import (
    ActionParams,
    GitRepoManager,
    K8sOperationType,
    KubernetesAnyChangeEvent,
    action,
    is_matching_diff,
    is_base64_encoded
)
import base64
import logging


class HelmReleaseParams(ActionParams):
    """
    todo add docs
    """

    namespace: str


@action
def helm_release_events(event: KubernetesAnyChangeEvent, action_params: HelmReleaseParams):
    """
    Audit Kubernetes resources from the cluster to Git as yaml files (cluster/namespace/resources hierarchy).
    Monitor resource changes and save it to a dedicated Git repository.

    Using this audit repository, you can easily detect unplanned changes on your clusters.
    """
