import logging

from robusta.api import ActionException, ErrorCodes, ExecutionBaseEvent, action

ROLLOUT_RESTART_DEPRECATED = "rollout_restart is deprecated and no longer supported"


@action
def rollout_restart(event: ExecutionBaseEvent):
    """
    Deprecated. This action is no longer supported and returns an error.
    """
    logging.error(ROLLOUT_RESTART_DEPRECATED)
    raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, ROLLOUT_RESTART_DEPRECATED)
