Kubernetes
############################

Basic triggers
----------------
Most Kubernetes resources can be used to trigger playbooks. The trigger will fire when the resource changes. For example:

**Pod triggers**:

* ``on_pod_create``
* ``on_pod_update``
* ``on_pod_delete``
* ``on_pod_all_changes``

The last trigger, ``on_pod_all_changes``, fires when any of the other triggers fires.

Supported resources
---------------------

The following resources are supported.

An example ``on_RESOURCE_create`` trigger is given for each one. The ``update``,
``delete``, and ``all_changes`` triggers are supported as well.

* Pod: on_pod_create
* ReplicaSet: on_replicaset_create
* DaemonSet: on_daemonset_create
* Deployment: on_deployment_create
* StatefulSet: on_statefulset_create
* Service: on_service_create
* Event: on_event_create
* HorizontalPodAutoscaler: on_horizontalpodautoscaler_create
* Node: on_node_create
* ClusterRole: on_clusterrole_create
* ClusterRoleBinding: on_clusterrolebinding_create
* Job: on_job_create
* Namespace: on_namespace_create
* ServiceAccount: on_serviceaccount_create

Wildcard triggers
--------------------

The following wildcard triggers will fire for any supported Kubernetes resource:

* on_kubernetes_any_resource_create
* on_kubernetes_any_resource_update
* on_kubernetes_any_resource_delete
* on_kubernetes_any_resource_all_changes
