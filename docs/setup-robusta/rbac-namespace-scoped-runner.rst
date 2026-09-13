.. _rbac-namespace-scoped-runner:

RBAC: Namespace-Scoped Runner
========================================

By default, the Robusta runner is a cluster-wide agent: it discovers workloads in every namespace,
reads cluster-scoped resources (nodes, namespaces, persistent volumes) and runs with a ``ClusterRole``
bound by a ``ClusterRoleBinding``.

This guide runs the runner with a **service account limited to a single namespace** — the namespace
Robusta is installed in. All the necessary behavior changes are controlled by environment variables,
so no Helm chart changes are required. Every variable defaults to today's cluster-wide behavior;
nothing changes unless you opt in.

What works and what doesn't
---------------------------

In this mode the runner keeps working as a platform agent: it connects to the Robusta platform,
reports cluster status (workload counts for its namespace, Kubernetes version, provider), answers
UI requests for resources **in its namespace**, and can reach Holmes and an explicitly-configured
Prometheus/Alertmanager.

The following are **not available** with a namespace-scoped service account:

- Cluster-wide resource discovery (the UI's apps/nodes/namespaces inventory) — disabled via ``DISABLE_DISCOVERY``.
- Kubernetes change tracking and ``on_kubernetes_*`` triggers — the kubewatch forwarder is disabled (see below).
- Playbooks. This setup assumes **all playbooks are disabled**. Many built-in actions need
  cluster-scoped access (nodes, persistent volumes, cluster-wide events and pod listings) and will
  fail with permission errors if invoked.
- Node-based features: node enrichments, drains, node count (reported as ``1``), auto-detection of
  the cluster provider (declare it with ``CLUSTER_PROVIDER`` instead).
- Auto-discovery of Prometheus/Alertmanager — set ``prometheus_url`` / ``alertmanager_url``
  explicitly, or disable the integration.

Environment variables
---------------------

Set these on the runner via ``runner.additional_env_vars`` in your Helm values:

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Default
     - Effect
   * - ``DISABLE_DISCOVERY``
     - ``false``
     - Disables the cluster-wide resource discovery loop.
   * - ``CLUSTER_STATS_NAMESPACE``
     - ``""``
     - When set, cluster-status workload counts are taken from this namespace only, and the node
       count is reported as ``1``. Also skips node listing in telemetry.
   * - ``DISABLE_PROMETHEUS_DISCOVERY``
     - ``false``
     - Never search the cluster for a Prometheus/Victoria Metrics service. Set ``prometheus_url``
       in ``globalConfig`` if you use Prometheus.
   * - ``DISABLE_ALERTMANAGER_DISCOVERY``
     - ``false``
     - Never search the cluster for an Alertmanager service. Set ``alertmanager_url`` in
       ``globalConfig`` if you use Alertmanager (e.g. for silences).
   * - ``HOLMES_DISCOVERY_NAMESPACE``
     - ``""``
     - Search for the Holmes service only in this namespace (instead of all namespaces).
       Alternatively set ``holmes_url`` in ``globalConfig``.
   * - ``CLUSTER_PROVIDER``
     - ``""``
     - Declare the cluster provider instead of detecting it from nodes. One of: ``GKE``, ``AKS``,
       ``EKS``, ``Kind``, ``Minikube``, ``RancherDesktop``, ``Kapsule``, ``Kops``,
       ``DigitalOcean``, ``OpenShift``, ``Unknown``.
   * - ``NAMESPACE_DATA_MODE``
     - ``cluster``
     - Where namespace labels/annotations (used by sink scopes) come from: ``cluster`` lists all
       namespaces, ``namespaced`` reads only the installation namespace, ``disabled`` makes no API
       call.
   * - ``ENABLE_TELEMETRY``
     - ``true``
     - Set ``false`` to disable the telemetry thread entirely (optional).

Step 1 — create the namespace-scoped service account
----------------------------------------------------

Create a ServiceAccount, Role and RoleBinding in Robusta's installation namespace (``robusta``
below — adjust to yours). The Role covers what the scoped runner needs at runtime: counting
workloads for cluster status, its scheduler-state ConfigMap, finding the Holmes service, and
reading its own namespace's metadata.

.. code-block:: yaml

    # runner-scoped-rbac.yaml
    apiVersion: v1
    kind: ServiceAccount
    metadata:
      name: robusta-runner-scoped
      namespace: robusta
    ---
    apiVersion: rbac.authorization.k8s.io/v1
    kind: Role
    metadata:
      name: robusta-runner-scoped
      namespace: robusta
    rules:
      # workload counts for cluster status + reading resources in this namespace from the UI
      - apiGroups: [""]
        resources:
          - pods
          - pods/status
          - pods/log
          - services
          - endpoints
          - configmaps
          - events
          - persistentvolumeclaims
          - serviceaccounts
          - replicationcontrollers
        verbs: ["get", "list", "watch"]
      - apiGroups: ["apps"]
        resources: ["deployments", "replicasets", "statefulsets", "daemonsets"]
        verbs: ["get", "list", "watch"]
      - apiGroups: ["batch"]
        resources: ["jobs", "cronjobs"]
        verbs: ["get", "list", "watch"]
      # the runner persists scheduler state in a ConfigMap named "scheduled-jobs"
      - apiGroups: [""]
        resources: ["configmaps"]
        verbs: ["create", "update", "patch"]
      # NAMESPACE_DATA_MODE=namespaced — a Role can grant `get` on the namespace it lives in
      - apiGroups: [""]
        resources: ["namespaces"]
        verbs: ["get"]
    ---
    apiVersion: rbac.authorization.k8s.io/v1
    kind: RoleBinding
    metadata:
      name: robusta-runner-scoped
      namespace: robusta
    roleRef:
      apiGroup: rbac.authorization.k8s.io
      kind: Role
      name: robusta-runner-scoped
    subjects:
      - kind: ServiceAccount
        name: robusta-runner-scoped
        namespace: robusta

.. code-block:: bash

    kubectl apply -f runner-scoped-rbac.yaml

.. note::

    If you want manual troubleshooting from the UI to work inside the namespace (fetching logs is
    already covered by ``pods/log`` above), you can additionally grant ``pods/exec`` (``get``,
    ``create``) and ``create``/``delete`` on ``pods`` and ``jobs``. Leave them out for a stricter
    setup — actions that lack permissions fail with a clear Kubernetes ``Forbidden`` error.

.. note::

    If you keep **Robusta-managed Prometheus alerts** (``enabledManagedConfiguration: true``)
    instead of disabling it in step 2, also add this rule to the Role — the runner syncs
    ``PrometheusRule`` CRs in its own namespace:

    .. code-block:: yaml

        - apiGroups: ["monitoring.coreos.com"]
          resources: ["prometheusrules"]
          verbs: ["get", "list", "create", "update", "patch", "delete"]

Step 2 — Helm values
--------------------

Point the chart at your service account, skip the chart's own cluster-wide RBAC, disable all
playbooks, and set the environment variables:

.. code-block:: yaml

    # scoped-values.yaml
    runner:
      # don't create the chart's ServiceAccount / ClusterRole / ClusterRoleBinding
      createServiceAccount: false
      # use the service account from step 1 instead
      customServiceAccount: robusta-runner-scoped
      additional_env_vars:
        - name: DISABLE_DISCOVERY
          value: "true"
        - name: CLUSTER_STATS_NAMESPACE
          value: "robusta"
        - name: DISABLE_PROMETHEUS_DISCOVERY
          value: "true"
        - name: DISABLE_ALERTMANAGER_DISCOVERY
          value: "true"
        - name: HOLMES_DISCOVERY_NAMESPACE
          value: "robusta"
        - name: CLUSTER_PROVIDER
          value: "EKS"          # your provider; or "OpenShift", "Unknown", ...
        - name: NAMESPACE_DATA_MODE
          value: "namespaced"   # or "disabled"
        - name: ENABLE_TELEMETRY
          value: "false"        # optional

    # no playbooks in this mode — many built-in actions need cluster-wide access
    builtinPlaybooks: []
    customPlaybooks: []
    enablePlatformPlaybooks: false

    # Robusta-managed Prometheus alerts sync PrometheusRule CRs in the installation
    # namespace. Disable it (your generated_values.yaml may have it enabled), or keep it
    # and grant the prometheusrules Role rule shown in step 1's note below.
    enabledManagedConfiguration: false

    # if you use Prometheus/Alertmanager, point at them explicitly instead of auto-discovery
    # globalConfig:
    #   prometheus_url: "http://prometheus.monitoring.svc.cluster.local:9090"
    #   alertmanager_url: "http://alertmanager.monitoring.svc.cluster.local:9093"

    # don't deploy the kubewatch forwarder at all (see the section below)
    kubewatch:
      enabled: false

Install into the same namespace the RBAC was created in:

.. code-block:: bash

    helm upgrade --install robusta robusta/robusta \
      -f generated_values.yaml \
      -f scoped-values.yaml \
      -n robusta

Disabling kubewatch
-------------------

The kubewatch forwarder is a separate Deployment with its own cluster-wide ``ClusterRole`` — it is
what watches the API server for changes and feeds them to the runner. ``kubewatch.enabled: false``
removes it entirely: the Deployment, Service, ConfigMap, ServiceAccount, ClusterRole and
ClusterRoleBinding are not rendered. Kubernetes change tracking and ``on_kubernetes_*`` triggers do
not work without it (which is consistent with this setup — playbooks are disabled anyway).

Verifying the scope
-------------------

.. code-block:: bash

    SA=system:serviceaccount:robusta:robusta-runner-scoped

    kubectl auth can-i list pods        --as=$SA -n robusta      # -> yes
    kubectl auth can-i list pods        --as=$SA -n kube-system  # -> no
    kubectl auth can-i list nodes       --as=$SA                 # -> no
    kubectl auth can-i list namespaces  --as=$SA                 # -> no

Then check the runner logs — there should be no recurring ``Forbidden`` (403) errors, and the
platform should show the cluster as connected, with workload counts for the scoped namespace and a
node count of 1.

Troubleshooting
---------------

**The runner exits with** ``configmaps "scheduled-jobs" is forbidden ... cannot get resource
"configmaps"`` — this permission IS part of the Role in step 1, so the RoleBinding is not matching
the pod's service account. This error is fatal (the runner restarts in a loop until fixed). Check,
in the installation namespace:

.. code-block:: bash

    NS=robusta   # your namespace
    SA=robusta-runner-scoped   # your service account name

    # 1. which service account is the pod actually running as?
    kubectl get deployment robusta-runner -n $NS \
      -o jsonpath='{.spec.template.spec.serviceAccountName}'

    # 2. does the RoleBinding reference the right Role and the right subject?
    kubectl get rolebinding -n $NS -o yaml | grep -B2 -A8 "$SA"

    # 3. the direct check:
    kubectl auth can-i get configmaps --as=system:serviceaccount:$NS:$SA -n $NS   # must be yes

Common causes: the RoleBinding's ``subjects[].name`` doesn't match the ServiceAccount name used in
``runner.customServiceAccount`` (e.g. after renaming one but not the other), the ``roleRef.name``
doesn't match the Role, or the objects were applied to a different namespace.

**Recurring** ``prometheusrules.monitoring.coreos.com is forbidden`` **errors ("An error occurred
while creating CR rules")** — Robusta-managed Prometheus alerts are enabled
(``enabledManagedConfiguration: true``, often present in ``generated_values.yaml``). Either set
``enabledManagedConfiguration: false`` as in step 2, or grant the ``prometheusrules`` Role rule
from the note in step 1. This error is not fatal, but it repeats every sync cycle.

Related guides
--------------

- :ref:`Read-Only Service Account <read-only-service-account>` — keep cluster-wide read access but
  remove all write permissions.
- :ref:`RBAC: Namespace-Scoped HolmesGPT <rbac-namespace-scoping>` — the equivalent setup for
  HolmesGPT.
