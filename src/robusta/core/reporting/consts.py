from enum import Enum

SYNC_RESPONSE_SINK = "robusta-synchronized-response-sink"


class FindingType(Enum):
    ISSUE = "issue"
    CONF_CHANGE = "configuration_change"
    HEALTH_CHECK = "health_check"
    REPORT = "report"


class FindingAggregationKey(Enum):
    NONE = None  # empty default
    CONFIGURATION_CHANGE_KUBERNETES_RESOURCE_CHANGE = "ConfigurationChange/KubernetesResource/Change"


# Finding sources
class FindingSource(Enum):
    NONE = None  # empty default
    KUBERNETES_API_SERVER = "kubernetes_api_server"
    PROMETHEUS = "prometheus"
    MANUAL = "manual"
    CALLBACK = "callback"
    SCHEDULER = "scheduler"


# Finding subject types
class FindingSubjectType(Enum):
    TYPE_NONE = None  # empty default
    TYPE_DEPLOYMENT = "deployment"
    TYPE_NODE = "node"
    TYPE_POD = "pod"
    TYPE_JOB = "job"
    TYPE_DAEMONSET = "daemonset"
    TYPE_STATEFULSET = "statefulset"
    TYPE_HPA = "horizontalpodautoscaler"

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
        elif kind == "statefulset":
            return FindingSubjectType.TYPE_STATEFULSET
        elif kind == "horizontalpodautoscaler":
            return FindingSubjectType.TYPE_HPA
        return FindingSubjectType.TYPE_NONE


# Annotations
class EnrichmentAnnotation(Enum):
    SCAN = "scan"


class SlackAnnotations:
    UNFURL = "unfurl"
    ATTACHMENT = "attachment"


class ScanType(str, Enum):
    POPEYE = "popeye"
    KRR = "krr"
