from enum import Enum

SYNC_RESPONSE_SINK = "robusta-synchronized-response-sink"


class FindingType(Enum):
    ISSUE = "issue"
    CONF_CHANGE = "configuration_change"
    HEALTH_CHECK = "health_check"
    REPORT = "report"


# Finding sources
class FindingSource(Enum):
    NONE = None  # empty default
    KUBERNETES_API_SERVER = "kubernetes_api_server"
    PROMETHEUS = "prometheus"
    MANUAL = "manual"
    CALLBACK = "callback"


# Finding subject types
class FindingSubjectType(Enum):
    TYPE_NONE = None  # empty default
    TYPE_DEPLOYMENT = "deployment"
    TYPE_NODE = "node"
    TYPE_POD = "pod"
    TYPE_JOB = "job"
    TYPE_DAEMONSET = "daemonset"

    @staticmethod
    def from_kind(kind: str):
        if kind == "deployment":
            return FindingSubjectType.TYPE_DEPLOYMENT
        elif kind == "node":
            return FindingSubjectType.TYPE_NODE
        elif kind == "pod":
            return FindingSubjectType.TYPE_POD
        elif kind == "job":
            return FindingSubjectType.TYPE_JOB
        elif kind == "daemonset":
            return FindingSubjectType.TYPE_DAEMONSET
        return FindingSubjectType.TYPE_NONE


# Annotations
class SlackAnnotations:
    UNFURL = "unfurl"
    ATTACHMENT = "attachment"
