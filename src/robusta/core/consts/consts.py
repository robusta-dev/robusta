import os
import uuid

# Relay target id
from enum import Enum

TARGET_ID = os.environ.get("RELAY_TARGET_ID", str(uuid.uuid4()))

# sink types
class SINK_TYPES(Enum):
    robusta = 1
    slack = 2
    kafka = 3


# Finding sources
SOURCE_KUBERNETES_API_SEVER = "kubernetes_api_server"
SOURCE_PROMETHEUS = "prometheus"
SOURCE_MANUAL = "manual"
SOURCE_CALLBACK = "callback"

# Finding types
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
SUBJECT_TYPE_DEPLOYMENT = "deployment"
SUBJECT_TYPE_NODE = "node"
SUBJECT_TYPE_POD = "pod"
