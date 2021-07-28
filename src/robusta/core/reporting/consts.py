# Relay target id
from enum import Enum

# sink types
class SINK_TYPES(Enum):
    robusta = "robusta"
    slack = "slack"
    kafka = "kafka"


# Finding sources
class FindingSource(Enum):
    SOURCE_NONE = "none"  # empty default
    SOURCE_KUBERNETES_API_SERVER = "kubernetes_api_server"
    SOURCE_PROMETHEUS = "prometheus"
    SOURCE_MANUAL = "manual"
    SOURCE_CALLBACK = "callback"


# Finding types
class FindingType(Enum):
    TYPE_NONE = "none"  # empty default
    TYPE_PROMETHEUS_ALERT = "prometheus/alert"
    TYPE_PROMETHEUS_CALLBACK = "prometheus/callback"
    TYPE_DEPLOYMENT_UPDATE = "deployment/update"
    TYPE_NODE_BASH = "node/bash"
    TYPE_POD_BASH = "pod/bash"
    TYPE_DEPLOYMENT_MISMATCH = "deployment/mismatch_analysis"
    TYPE_MANUAL_ENRICHMENT = "manual/enrichment"
    TYPE_ENRICHMENT_PROFILING = "enrichment/profiling"
    TYPE_KUBERNETES_CRASH = "kubernetes/crash"
    TYPE_CHAOS_STRESS = "chaos/stress"


# Finding subject types
class FindingSubjectType(Enum):
    SUBJECT_TYPE_NONE = "none"
    SUBJECT_TYPE_DEPLOYMENT = "deployment"
    SUBJECT_TYPE_NODE = "node"
    SUBJECT_TYPE_POD = "pod"
    SUBJECT_TYPE_JOB = "job"
    SUBJECT_TYPE_DAEMONSET = "daemonset"


# Annotations
class SlackAnnotations:
    UNFURL = "unfurl"
    ATTACHMENT = "attachment"
