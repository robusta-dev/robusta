# This file was autogenerated. Do not edit.

from hikaru.model.rel_1_16.v2beta1 import *

from robusta.integrations.kubernetes.custom_models import RobustaDeployment, RobustaJob, RobustaPod

KIND_TO_MODEL_CLASS = {
    "Pod": RobustaPod,
    "ReplicaSet": ReplicaSet,
    "DaemonSet": DaemonSet,
    "Deployment": RobustaDeployment,
    "StatefulSet": StatefulSet,
    "Service": Service,
    "Event": Event,
    "HorizontalPodAutoscaler": HorizontalPodAutoscaler,
    "Node": Node,
    "ClusterRole": ClusterRole,
    "ClusterRoleBinding": ClusterRoleBinding,
    "Job": RobustaJob,
    "Namespace": Namespace,
    "ServiceAccount": ServiceAccount,
    "PersistentVolume": PersistentVolume,
    "ConfigMap": ConfigMap,
}
