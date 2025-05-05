from typing import ClassVar
from pydantic.dataclasses import dataclass
from hikaru.model.rel_1_26 import HikaruDocumentBase, ObjectMeta, LabelSelector
import datetime
import pytz
from kubernetes import client
from hikaru.crd import HikaruCRDDocumentMixin


@dataclass
class CRDBase:
    plural: ClassVar[str] = ""
    group: ClassVar[str] = ""
    version: ClassVar[str] = ""
    total_pods_path: ClassVar[str] = ""
    ready_pods_path: ClassVar[str] = ""

    metadata: ObjectMeta
    spec: dict
    status: dict
    apiVersion: str
    kind: str

    @classmethod
    def readNamespaced(cls, name: str, namespace: str):
        obj = client.CustomObjectsApi().get_namespaced_custom_object(
            cls.group, cls.version, namespace, cls.plural, name
        )
        obj = cls(**obj)
        return type("", (object,), {"obj": obj})()

    @classmethod
    def rollout_restart_patch(cls):
        return {
            "metadata": {
                "annotations": {
                    "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow()
                    .replace(tzinfo=pytz.UTC)
                    .isoformat()
                }
            }
        }

    @classmethod
    def list_namespaced(cls, namespace: str):
        crd_res = client.CustomObjectsApi().list_namespaced_custom_object(
            group=cls.group,
            version=cls.version,
            namespace=namespace,
            plural=cls.plural,
        )
        crd_list = type(
            "",
            (object,),
            {"items": [cls(**crd) for crd in crd_res.get("items", [])]},
        )()

        return crd_list

    @classmethod
    def list_for_all_namespaces(cls):
        crd_res = client.CustomObjectsApi().list_cluster_custom_object(
            group=cls.group,
            version=cls.version,
            plural=cls.plural,
        )
        crd_list = type(
            "",
            (object,),
            {"items": [cls(**crd) for crd in crd_res.get("items", [])]},
        )()

        return crd_list


# https://github.com/orgs/strimzi/discussions/9140 // restarts
# https://github.com/strimzi/strimzi-kafka-operator/blob/main/helm-charts/helm3/strimzi-kafka-operator/crds/042-Crd-strimzipodset.yaml
@dataclass
class StrimziPodSet(CRDBase, HikaruDocumentBase, HikaruCRDDocumentMixin):
    plural: ClassVar[str] = "strimzipodsets"
    group: ClassVar[str] = "core.strimzi.io"
    version: ClassVar[str] = "v1beta2"
    name: ClassVar[str] = "StrimziPodSet"
    total_pods_path: ClassVar[str] = "status/pods"
    ready_pods_path: ClassVar[str] = "status/readyPods"

    def __post_init__(self):
        self.spec["selector"] = LabelSelector(**self.spec["selector"])

    @classmethod
    def rollout_restart_patch(cls):
        return {
            "metadata": {"annotations": {"strimzi.io/manual-rolling-update": "true"}}
        }


# https://github.com/search?q=repo%3Acloudnative-pg/cloudnative-pg%20ClusterRestartAnnotationName&type=code // restart
# https://cloudnative-pg.io/documentation/1.20/cloudnative-pg.v1/#postgresql-cnpg-io-v1-Cluster crd.
@dataclass
class Cluster(CRDBase, HikaruDocumentBase, HikaruCRDDocumentMixin):
    plural: ClassVar[str] = "clusters"
    group: ClassVar[str] = "postgresql.cnpg.io"
    version: ClassVar[str] = "v1"
    name: ClassVar[str] = "Cluster"
    total_pods_path: ClassVar[str] = "spec/instances"
    ready_pods_path: ClassVar[str] = "status/readyInstances"

    def __post_init__(self):
        self.spec["selector"] = {"cnpg.io/cluster": self.metadata.get("name")}


@dataclass
class ExecutionContext(CRDBase, HikaruDocumentBase, HikaruCRDDocumentMixin):
    plural: ClassVar[str] = "executioncontexts"
    group: ClassVar[str] = "hub.knime.com"
    version: ClassVar[str] = "v1alpha1"
    name: ClassVar[str] = "ExecutionContext"
    total_pods_path: ClassVar[str] = "spec/executor/replicaCount"
    ready_pods_path: ClassVar[str] = "status/readyReplicas"

    def __post_init__(self):
        self.spec["selector"] = {"app.kubernetes.io/instance": self.metadata.get("name")}


# this map is registered into trigger events(LOADERS_MAPPINGS) and Listers(for comparisons)
CRDS_map = {
    "StrimziPodSet": StrimziPodSet,
    "Cluster": Cluster,
    "ExecutionContext": ExecutionContext,
}
