import logging

from robusta.api import ActionException, ErrorCodes, ExecutionBaseEvent, action

POD_BASH_ENRICHER_DEPRECATED = "pod_bash_enricher is deprecated and no longer supported"
NODE_BASH_ENRICHER_DEPRECATED = "node_bash_enricher is deprecated and no longer supported"


@action
def pod_bash_enricher(event: ExecutionBaseEvent):
    """
    Deprecated. This action is no longer supported and returns an error.
    """
    logging.error(POD_BASH_ENRICHER_DEPRECATED)
    raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, POD_BASH_ENRICHER_DEPRECATED)


@action
def node_bash_enricher(event: ExecutionBaseEvent):
    """
    Deprecated. This action is no longer supported and returns an error.
    """
    logging.error(NODE_BASH_ENRICHER_DEPRECATED)
    raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, NODE_BASH_ENRICHER_DEPRECATED)
