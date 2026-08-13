from robusta.core.model.env_vars import CREATE_PERMISSIONS_DISABLED
from robusta.utils.error_codes import ActionException, ErrorCodes


def check_create_permissions():
    """
    Raise if the runner was installed without create permissions
    (Helm value runner.rbac.namespacedCreate=false), so actions that create
    pods/jobs/secrets/deployments fail fast with a clear error instead of a K8s 403.
    """
    if CREATE_PERMISSIONS_DISABLED:
        raise ActionException(
            ErrorCodes.RESOURCE_NOT_PERMITTED,
            "This action is disabled because the runner was installed without create permissions "
            "(runner.rbac.namespacedCreate=false in the Robusta Helm values). "
            "Set runner.rbac.namespacedCreate=true to enable it.",
        )
