from robusta.api import *

from pydantic.main import BaseModel


class GitAuditParams(BaseModel):
    cluster_name: str
    git_https_url: str
    git_user: str
    git_password: str

    def __str__(self):
        return f"cluster_name={self.cluster_name} git_https_url={self.git_https_url} git_user=***** git_password=*****"


def git_safe_name(name):
    return re.sub("[^0-9a-zA-Z\\-]+", "-", name)

skipped_kinds = ["Event"]

@on_kubernetes_any_all_changes
def git_change_audit(event : KubernetesAnyEvent, action_params: GitAuditParams):
    """Save a configuration copy to git"""
    if event.obj.kind in skipped_kinds:
        return

    if len(event.obj.metadata.ownerReferences) != 0:
        return # not handling runtime objects

    git_repo = GitRepoManager.get_git_repo(action_params.git_https_url, action_params.git_user, action_params.git_password)
    name = f"{git_safe_name(event.obj.metadata.name)}.yaml"
    namespace = event.obj.metadata.namespace or "None"
    path = f"{git_safe_name(action_params.cluster_name)}/{git_safe_name(namespace)}"

    if event.operation == K8sOperationType.DELETE:
        git_repo.delete_push(path, name)
    elif event.operation == K8sOperationType.CREATE:
        obj_yaml = hikaru.get_yaml(event.obj.spec)
        git_repo.commit_push(obj_yaml, path, name, f"Create {event.obj.kind} named {event.obj.metadata.name} on namespace {namespace}")
    else: # update
        obj_yaml = hikaru.get_yaml(event.obj.spec)
        old_obj_yaml = ""
        if event.old_obj is not None:
            old_obj_yaml = hikaru.get_yaml(event.old_obj.spec)
        if obj_yaml != old_obj_yaml: # we have a change in the spec
            git_repo.commit_push(obj_yaml, path, name, f"Update {event.obj.kind} named {event.obj.metadata.name} on namespace {namespace}")
