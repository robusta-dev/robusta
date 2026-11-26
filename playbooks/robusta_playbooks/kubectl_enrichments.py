import logging

from robusta.api import ExecutionBaseEvent, PodRunningParams, action
from robusta.utils.error_codes import ActionException, ErrorCodes

KUBECTL_COMMAND_DEPRECATED = "kubectl_command is deprecated and no longer supported"


class KubectlParams(PodRunningParams):
    """
    :var command: The full kubectl command to run, formatted as a shell command string.
    :var description: A description of the command ran.
    :var timeout: The maximum time (in seconds) to wait for the kubectl command to complete. Default is 3600 seconds.
    """

    command: str = None
    description: str = None
    timeout: int = 3600


@action(command_action=True)
def kubectl_command(event: ExecutionBaseEvent, params: KubectlParams):
    """
    Deprecated. This action is no longer supported and returns an error.
    """
    logging.error(KUBECTL_COMMAND_DEPRECATED)
    raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, KUBECTL_COMMAND_DEPRECATED)
