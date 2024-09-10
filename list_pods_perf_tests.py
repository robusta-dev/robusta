import time
from kubernetes import client, config
import hikaru
import kubernetes.client.exceptions
from hikaru.model.rel_1_26 import ContainerState, ContainerStateTerminated, ContainerStatus, Pod, PodList


# Load Kubernetes configuration
config.load_kube_config()

# Define namespace and label selector
namespace = "default"  # Replace with your namespace
label_selector = "app=nginx"

# Create an instance of the API class
v1 = client.CoreV1Api()


#x= client.CoreV1Api().read_namespaced_pod(
#            namespace="default",
#            name="robusta-prometheus-node-exporter-kmchk",
#        )

start_time = time.time()
resp = v1.list_namespaced_pod(
    namespace=namespace, 
    label_selector=label_selector,
    limit=10
)
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Time taken to list pretty pods: {elapsed_time:.4f} seconds")

# non-pretty
start_time = time.time()
resp = v1.list_namespaced_pod(
    namespace=namespace, 
    label_selector=label_selector,
)
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Time taken to list pods: {elapsed_time:.4f} seconds")

start_time = time.time()
hikaru_result = PodList.listNamespacedPod(namespace="default", label_selector=label_selector).obj.items
end_time = time.time()
elapsed_time = end_time - start_time
# Print the elapsed time
print(f"Time taken to list pods with hikaru: {elapsed_time:.4f} seconds")
