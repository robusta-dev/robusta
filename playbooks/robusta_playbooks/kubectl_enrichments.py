import logging

from robusta.api import ExecutionBaseEvent, action
from robusta.utils.error_codes import ActionException, ErrorCodes

KUBECTL_COMMAND_DEPRECATED = "kubectl_command is deprecated and no longer supported"


@action
def kubectl_command(event: ExecutionBaseEvent):
    """
    Deprecated. This action is no longer supported and returns an error.
    """
    logging.error(KUBECTL_COMMAND_DEPRECATED)
    raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, KUBECTL_COMMAND_DEPRECATED)
