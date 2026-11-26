import logging

from robusta.api import ActionException, ErrorCodes, ExecutionBaseEvent, action

CLEANUP_ROBUSTA_PODS_DEPRECATED = "cleanup_robusta_pods is deprecated and no longer supported"


@action
def cleanup_robusta_pods(event: ExecutionBaseEvent):
    """
    Deprecated. This action is no longer supported and returns an error.
    """
    logging.error(CLEANUP_ROBUSTA_PODS_DEPRECATED)
    raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, CLEANUP_ROBUSTA_PODS_DEPRECATED)
