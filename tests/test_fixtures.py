# this doesn't test robusta, it tests fixtures like `kind_cluster` which were implemented for the testing system
# itself
import subprocess
from kubernetes import client


def test_kind_cluster(kind_cluster):
    # Getting the API instance
    v1 = client.CoreV1Api()

    # Listing all pods in all namespaces
    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        print(f"{i.status.pod_ip}\t{i.metadata.namespace}\t{i.metadata.name}")

    # Subprocess call
    pods = subprocess.check_output(["kubectl", "get", "pods", "--all-namespaces"])
    print(pods.decode())
