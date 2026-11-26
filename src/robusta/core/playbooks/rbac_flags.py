from robusta.utils.error_codes import ActionException, ErrorCodes

RBAC_FLAGS_DOCS_URL = "https://docs.robusta.dev/master/setup-robusta/read-only-service-account.html"


def disabled_flag_message(flag_name: str) -> str:
    return f"Not supported while runner.rbac.{flag_name} is false. To enable it, see {RBAC_FLAGS_DOCS_URL}"


def require_rbac_flag(enabled: bool, flag_name: str):
    if not enabled:
        raise ActionException(ErrorCodes.RESOURCE_NOT_PERMITTED, disabled_flag_message(flag_name))


def reject_job_creation():
    raise ActionException(ErrorCodes.RESOURCE_NOT_PERMITTED, f"Actions that create Jobs are not supported, see {RBAC_FLAGS_DOCS_URL}")
