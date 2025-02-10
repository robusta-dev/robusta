
.. kubernetes:

Kubernetes Toolsets
==================


Core
-------------------

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
    holmes:
        toolsets:
            kubernetes/core:
                enabled: true



.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - kubectl_describe
     - Run kubectl describe command on a specific resource
   * - kubectl_get_by_name
     - Get details of a specific resource with labels
   * - kubectl_get_by_kind_in_namespace
     - List all resources of a given type in a namespace
   * - kubectl_get_by_kind_in_cluster
     - List all resources of a given type across the cluster
   * - kubectl_find_resour
     - Search for resources matching a keyword
   * - kubectl_get_yaml
     - Get YAML definition of a resource
   * - kubectl_events
     - Get events for a specific resource
   * - kubectl_memory_requests_all_namespaces
     - Get memory requests for all pods across all namespaces in MiB
   * - kubectl_memory_requests_namespace
     - Get memory requests for all pods in a specific namespace in MiB
   * - kubernetes_jq_query
     - Query Kubernetes resources using jq filters


Logs
--------------------

Read kubernetes pod logs.

.. code-block:: yaml

    holmes:
        toolsets:
            kubernetes/logs:
                enabled: true

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - kubectl_previous_logs
     - Run `kubectl logs --previous` on a single Kubernetes pod. Used to fetch logs for a pod that crashed and see logs from before the crash. Never give a deployment name or a resource that is not a pod.
   * - kubectl_previous_logs_all_containers
     - Run `kubectl logs --previous` on a single Kubernetes pod. Used to fetch logs for a pod that crashed and see logs from before the crash.
   * - kubectl_container_previous_logs
     - Run `kubectl logs --previous` on a single container of a Kubernetes pod. Used to fetch logs for a pod that crashed and see logs from before the crash.
   * - kubectl_logs
     - Run `kubectl logs` on a single Kubernetes pod. Never give a deployment name or a resource that is not a pod.
   * - kubectl_logs_all_containers
     - Run `kubectl logs` on all containers within a single Kubernetes pod.
   * - kubectl_container_logs
     - Run `kubectl logs` on a single container within a Kubernetes pod. This is to get the logs of a specific container in a multi-container pod.
   * - kubectl_logs_grep
     - Search for a specific term in the logs of a single Kubernetes pod. Only provide a pod name, not a deployment or other resource.
   * - kubectl_logs_all_containers_grep
     - kubectl logs {{pod_name}} -n {{ namespace }} --all-containers | grep {{ search_term }}


Live metrics
----------------

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
    holmes:
        toolsets:
            kubernetes/live-metrics:
                enabled: true

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - kubectl_top_pods
     - Get real-time CPU and memory usage for all pods
   * - kubectl_top_nodes
     - Get real-time CPU and memory usage for all nodes

Prometheus stack
--------------------

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    holmes:
        toolsets:
            kubernetes/kube-prometheus-stack:
                enabled: true

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - get_prometheus_target
     - Get Prometheus target definition


Resource Lineage Extras (with krew)
--------------------

Fetches children/dependents and parents/dependencies resources using kube-lineage installed via `kubectl krew`.
To make this toolset work, install kube-lineage with krew.

.. code-block:: yaml

    holmes:
        toolsets:
            kubernetes/kubernetes/krew-extras:
                enabled: true

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - kubectl_lineage_children
     - Get all children/dependents of a Kubernetes resource, recursively, including their status
   * - kubectl_lineage_parents
     - Get all parents/dependencies of a Kubernetes resource, recursively, including their status


Resource Lineage Extras (from source)
--------------------

Fetches children/dependents and parents/dependencies resources using kube-lineage.
To make this work, build kube-lineage from source.

.. code-block:: yaml

    holmes:
        toolsets:
            kubernetes/kube-lineage-extras:
                enabled: true

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - kubectl_lineage_children
     - Get all children/dependents of a Kubernetes resource, recursively, including their status
   * - kubectl_lineage_parents
     - Get all parents/dependencies of a Kubernetes resource, recursively, including their status
