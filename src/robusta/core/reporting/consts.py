# Relay target id
from enum import Enum

# sink types
class SinkType(Enum):
    ROBUSTA = "robusta"
    SLACK = "slack"
    KAFKA = "kafka"


# Finding sources
class FindingSource(Enum):
    NONE = "none"  # empty default
    KUBERNETES_API_SERVER = "kubernetes_api_server"
    PROMETHEUS = "prometheus"
    MANUAL = "manual"
    CALLBACK = "callback"


# Finding types
class FindingType(Enum):
    NONE = "none"  # empty default
    PROMETHEUS_ALERT = "prometheus/alert"
    PROMETHEUS_CALLBACK = "prometheus/callback"
    DEPLOYMENT_UPDATE = "deployment/update"
    NODE_BASH = "node/bash"
    POD_BASH = "pod/bash"
    DEPLOYMENT_MISMATCH = "deployment/mismatch_analysis"
    MANUAL_ENRICHMENT = "manual/enrichment"
    ENRICHMENT_PROFILING = "enrichment/profiling"
    KUBERNETES_CRASH = "kubernetes/crash"
    CHAOS_STRESS = "chaos/stress"


# Finding subject types
class FindingSubjectType(Enum):
    TYPE_NONE = "none"
    TYPE_DEPLOYMENT = "deployment"
    TYPE_NODE = "node"
    TYPE_POD = "pod"
    TYPE_JOB = "job"
    TYPE_DAEMONSET = "daemonset"


# Annotations
class SlackAnnotations:
    UNFURL = "unfurl"
    ATTACHMENT = "attachment"
