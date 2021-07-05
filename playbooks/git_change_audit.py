from robusta.api import *

from pydantic.main import BaseModel


class GitAuditParams(BaseModel):
    cluster_name: str
    git_url: str
    git_key: str
    ignored_changes: List[str] = []

    def __str__(self):
        return f"cluster_name={self.cluster_name} git_url={self.git_url} git_key=*****"


def git_safe_name(name):
    return re.sub("[^0-9a-zA-Z\\-]+", "-", name)

skipped_kinds = ["Event"]


def obj_diff(spec: HikaruBase, old_spec: HikaruBase, ignored_changes: List[str]) -> bool:
    if old_spec is None:
        return True

    all_diffs = spec.diff(old_spec)
    formatted_diffs = [diff.formatted_path[diff.formatted_path.index(".") + 1:] for diff in all_diffs if diff.formatted_path]
    filtered_diffs = [diff for diff in formatted_diffs if diff not in ignored_changes]
    return len(filtered_diffs) > 0


@on_kubernetes_any_resource_all_changes
def git_change_audit(event : KubernetesAnyEvent, action_params: GitAuditParams):
    """Save a configuration copy to git"""
    if event.obj.kind in skipped_kinds:
        return

    if len(event.obj.metadata.ownerReferences) != 0:
        return # not handling runtime objects

    git_repo = GitRepoManager.get_git_repo(action_params.git_url, action_params.git_key)
    name = f"{git_safe_name(event.obj.metadata.name)}.yaml"
    namespace = event.obj.metadata.namespace or "None"
    path = f"{git_safe_name(action_params.cluster_name)}/{git_safe_name(namespace)}"

    if event.operation == K8sOperationType.DELETE:
        git_repo.delete_push(path, name)
    elif event.operation == K8sOperationType.CREATE:
        obj_yaml = hikaru.get_yaml(event.obj.spec)
        git_repo.commit_push(obj_yaml, path, name, f"Create {event.obj.kind} named {event.obj.metadata.name} on namespace {namespace}")
    else: # update
        old_spec = event.old_obj.spec if event.old_obj else None
        if obj_diff(event.obj.spec, old_spec, action_params.ignored_changes): # we have a change in the spec
            git_repo.commit_push(hikaru.get_yaml(event.obj.spec), path, name,
                                 f"Update {event.obj.kind} named {event.obj.metadata.name} on namespace {namespace}")
