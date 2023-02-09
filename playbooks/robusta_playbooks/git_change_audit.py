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


class GitAuditParams(ActionParams):
    """
    :var cluster_name: This cluster name. Changes will be audited under this cluster name.
    :var git_url: Audit Git repository url.
    :var git_key: Git repository deployment key with *write* access. To set this up `generate a private/public key pair for GitHub <https://docs.github.com/en/developers/overview/managing-deploy-keys#setup-2>`_.
    :var ignored_changes: List of changes that shouldn't be audited.

    :example git_url: "git@github.com:arikalon1/robusta-audit.git"
    """

    def post_initialization(self):
        secret_key = self.git_key.get_secret_value()

        if is_base64_encoded(secret_key): 
            self.git_key = SecretStr(base64.b64decode(secret_key).decode("utf-8"))
        else:
            self.git_key = SecretStr(secret_key)

    cluster_name: str
    git_url: str
    git_key: SecretStr
    ignored_changes: List[str] = []

    def __str__(self):
        return f"cluster_name={self.cluster_name} git_url={self.git_url} git_key=*****"


def git_safe_name(name):
    return re.sub("[^0-9a-zA-Z\\-]+", "-", name)


# kinds with no 'spec'
skipped_kinds: List[str] = [
    "Event",
    "ClusterRole",
    "ClusterRoleBinding",
    "ServiceAccount",
    "ConfigMap"
]


def obj_diff(spec: HikaruBase, old_spec: HikaruBase, ignored_changes: List[str]) -> bool:
    if old_spec is None:
        return True

    all_diffs = spec.diff(old_spec)
    filtered_diffs = list(filter(lambda x: not is_matching_diff(x, ignored_changes), all_diffs))
    return len(filtered_diffs) > 0


@action
def git_change_audit(event: KubernetesAnyChangeEvent, action_params: GitAuditParams):
    """
    Audit Kubernetes resources from the cluster to Git as yaml files (cluster/namespace/resources hierarchy).
    Monitor resource changes and save it to a dedicated Git repository.

    Using this audit repository, you can easily detect unplanned changes on your clusters.
    """
    try:
        if event.obj.kind in skipped_kinds:
            return

        if len(event.obj.metadata.ownerReferences) != 0:
            return  # not handling runtime objects

        git_repo = GitRepoManager.get_git_repo(
            action_params.git_url,
            action_params.git_key.get_secret_value(),
        )
        name = f"{git_safe_name(event.obj.metadata.name)}.yaml"
        namespace = event.obj.metadata.namespace or "None"
        path = f"{git_safe_name(action_params.cluster_name)}/{git_safe_name(namespace)}"

        if event.operation == K8sOperationType.DELETE:
            git_repo.delete_push(path, name, f"Delete {path}/{name}", action_params.cluster_name)
        elif event.operation == K8sOperationType.CREATE:
            obj_yaml = hikaru.get_yaml(event.obj.spec)
            git_repo.commit_push(
                obj_yaml,
                path,
                name,
                f"Create {event.obj.kind} named {event.obj.metadata.name} on namespace {namespace}",
                action_params.cluster_name,
            )
        else:  # update
            old_spec = event.old_obj.spec if event.old_obj else None
            if obj_diff(event.obj.spec, old_spec, action_params.ignored_changes):  # we have a change in the spec
                git_repo.commit_push(
                    hikaru.get_yaml(event.obj.spec),
                    path,
                    name,
                    f"Update {event.obj.kind} named {event.obj.metadata.name} on namespace {namespace}",
                    action_params.cluster_name,
                )
    except Exception as e:
        logging.exception(e)
        logging.error("git audit error", exc_info=True)
