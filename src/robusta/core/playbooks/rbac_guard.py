from robusta.core.model.env_vars import CREATE_PERMISSIONS_DISABLED
from robusta.utils.error_codes import ActionException, ErrorCodes


def check_create_permissions():
    if CREATE_PERMISSIONS_DISABLED:
        raise ActionException(
            ErrorCodes.RESOURCE_NOT_PERMITTED,
            "This action is disabled because the runner was installed without create permissions "
            "(runner.rbac.namespacedCreate=false in the Robusta Helm values). "
            "Set runner.rbac.namespacedCreate=true to enable it.",
        )
