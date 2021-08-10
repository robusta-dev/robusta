# Relay target id
from enum import Enum

# sink types
class SinkType(Enum):
    ROBUSTA = "robusta"
    SLACK = "slack"
    KAFKA = "kafka"
    DATADOG = "datadog"


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


# Annotations
class SlackAnnotations:
    UNFURL = "unfurl"
    ATTACHMENT = "attachment"
