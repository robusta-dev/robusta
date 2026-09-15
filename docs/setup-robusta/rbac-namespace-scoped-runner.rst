.. _rbac-namespace-scoped-runner:

RBAC: Namespace-Scoped Runner
========================================

By default, the Robusta runner is a cluster-wide agent: it discovers workloads in every namespace,
reads cluster-scoped resources (nodes, namespaces, persistent volumes) and runs with a ``ClusterRole``
bound by a ``ClusterRoleBinding``.

This guide runs the runner with **access limited to a single namespace** — the namespace Robusta is
installed in. Setting ``runner.rbac.namespaceScoped: true`` makes the chart render namespaced RBAC
(a ``Role`` + ``RoleBinding`` instead of the ClusterRole + ClusterRoleBinding) and presets the
runner's scoped-mode environment variables. Everything stays Helm-managed — no hand-applied RBAC —
and because all rendered objects are namespaced, you can install **multiple independent Robusta
instances in different namespaces** without name collisions. The default (``false``) keeps today's
cluster-wide behavior.

What works and what doesn't
---------------------------

In this mode the runner keeps working as a platform agent: it connects to the Robusta platform,
reports cluster status (workload counts for its namespace, Kubernetes version, provider), answers
UI requests for resources **in its namespace**, and can reach Holmes and an explicitly-configured
Prometheus/Alertmanager. The runner also **self-registers** its own and the Holmes deployments with
the platform on the regular discovery cadence, so the UI's Agents page works — live status, pod
states, uptime, and the log links — even though full discovery is off.

The following are **not available** with a namespace-scoped service account:

- Cluster-wide resource discovery (the UI's apps/nodes/namespaces inventory) — disabled via
  ``DISABLE_DISCOVERY``. Only the self-registered robusta-runner and Holmes deployments appear
  under the cluster's services.
- Kubernetes change tracking and ``on_kubernetes_*`` triggers — the kubewatch forwarder is disabled (see below).
- Playbooks. This setup assumes **all playbooks are disabled**. Many built-in actions need
  cluster-scoped access (nodes, persistent volumes, cluster-wide events and pod listings) and will
  fail with permission errors if invoked.
- Node-based features: node enrichments, drains, node count (reported as ``1``), auto-detection of
  the cluster provider (declare it with ``CLUSTER_PROVIDER`` instead).
- Auto-discovery of Prometheus/Alertmanager — set ``prometheus_url`` / ``alertmanager_url``
  explicitly, or leave them unset to run without those integrations.

Setup
-----

Add the following to your Helm values:

.. code-block:: yaml

    # scoped-values.yaml
    runner:
      rbac:
        # renders a namespaced Role + RoleBinding (no ClusterRole/ClusterRoleBinding)
        # and presets the scoped-mode env vars listed below
        namespaceScoped: true
      additional_env_vars:
        - name: CLUSTER_PROVIDER
          value: "EKS"          # your provider; or "OpenShift", "Unknown", ...
        - name: ENABLE_TELEMETRY
          value: "false"        # optional

    # no playbooks in this mode — many built-in actions need cluster-wide access
    builtinPlaybooks: []
    customPlaybooks: []
    enablePlatformPlaybooks: false

    # Robusta-managed Prometheus alerts sync PrometheusRule CRs in the installation
    # namespace. Disable it (your generated_values.yaml may have it enabled), or keep it
    # and grant the prometheusrules rule via runner.customClusterRoleRules (see note below).
    enabledManagedConfiguration: false

    # if you use Prometheus/Alertmanager, point at them explicitly instead of auto-discovery
    # globalConfig:
    #   prometheus_url: "http://prometheus.monitoring.svc.cluster.local:9090"
    #   alertmanager_url: "http://alertmanager.monitoring.svc.cluster.local:9093"

    # don't deploy the kubewatch forwarder at all (see the section below)
    kubewatch:
      enabled: false

Then install:

.. code-block:: bash

    helm upgrade --install robusta robusta/robusta \
      -f generated_values.yaml \
      -f scoped-values.yaml \
      -n robusta --create-namespace

For multiple instances, repeat per namespace with a **unique** ``clusterName`` per install (each
instance appears as its own cluster in the Robusta platform).

What ``runner.rbac.namespaceScoped`` does
-----------------------------------------

**RBAC** — instead of ``<release>-runner-cluster-role`` (ClusterRole) + ClusterRoleBinding, the
chart renders ``<release>-runner-role`` (a namespaced ``Role`` with the same rules) bound by a
``RoleBinding`` in the release namespace. The ServiceAccount and the namespaced create-permissions
Role (``<release>-runner-local-role``) are unchanged. Because a Role is namespaced, multiple
installs — even with the same release name — cannot collide on cluster-scoped RBAC objects.

**Environment variables** — the flag presets these on the runner (any entry you add to
``runner.additional_env_vars`` with the same name overrides the preset):

.. list-table::
   :header-rows: 1
   :widths: 32 23 45

   * - Variable
     - Preset by the flag
     - Effect
   * - ``DISABLE_DISCOVERY``
     - ``true``
     - Disables the cluster-wide resource discovery loop.
   * - ``CLUSTER_STATS_NAMESPACE``
     - the release namespace
     - Cluster-status workload counts are taken from this namespace only; the node count is
       reported as ``1`` and telemetry skips node listing. Together with ``DISABLE_DISCOVERY``,
       it also enables self-registration: the runner publishes its own and the Holmes deployments
       from this namespace, keeping the UI's Agents page (status, pods, logs) working.
   * - ``NAMESPACE_DATA_MODE``
     - ``namespaced``
     - Namespace labels/annotations (used by sink scopes) are read only for the installation
       namespace. Other values: ``cluster`` (all namespaces), ``disabled`` (no API call).
   * - ``HOLMES_DISCOVERY_NAMESPACE``
     - the release namespace
     - Search for the Holmes service only in this namespace. Alternatively set ``holmes_url``
       in ``globalConfig``.
   * - ``DISABLE_PROMETHEUS_DISCOVERY``
     - ``true``
     - Never search the cluster for a Prometheus/Victoria Metrics service. Set ``prometheus_url``
       in ``globalConfig`` if you use Prometheus.
   * - ``DISABLE_ALERTMANAGER_DISCOVERY``
     - ``true``
     - Never search the cluster for an Alertmanager service. Set ``alertmanager_url`` in
       ``globalConfig`` if you use Alertmanager (e.g. for silences).
   * - ``CLUSTER_PROVIDER``
     - not preset
     - Declare the cluster provider instead of detecting it from nodes. One of: ``GKE``, ``AKS``,
       ``EKS``, ``Kind``, ``Minikube``, ``RancherDesktop``, ``Kapsule``, ``Kops``,
       ``DigitalOcean``, ``OpenShift``, ``Unknown``. Recommended — without it the provider shows
       as ``Unknown``.
   * - ``ENABLE_TELEMETRY``
     - not preset
     - Set ``false`` to disable the telemetry thread entirely (optional).

.. note::

    The Role carries the same rules as the default ClusterRole, so cluster-scoped entries in it
    (``nodes``, ``persistentvolumes``, ...) are legal but grant nothing — a RoleBinding
    structurally cannot grant cluster-scoped access. One side effect: ``kubectl auth can-i list
    nodes -n <ns>`` may answer ``yes`` even though a real ``kubectl get nodes`` is denied; check
    without ``-n`` (as in the verification below) for the true answer.

.. note::

    If you keep **Robusta-managed Prometheus alerts** (``enabledManagedConfiguration: true``),
    also add this to your values — the runner syncs ``PrometheusRule`` CRs in its own namespace,
    and ``customClusterRoleRules`` entries are added to the scoped Role:

    .. code-block:: yaml

        runner:
          customClusterRoleRules:
            - apiGroups: ["monitoring.coreos.com"]
              resources: ["prometheusrules"]
              verbs: ["get", "list", "create", "update", "patch", "delete"]

Alternative: bring your own service account
-------------------------------------------

If your security process requires RBAC managed outside the chart, set
``runner.createServiceAccount: false`` (nothing RBAC-related is rendered) plus
``runner.customServiceAccount: <name>``, and create the ServiceAccount, a Role with the rules the
runner needs (workload reads for cluster stats, ``configmaps`` ``get/create/update`` for the
``scheduled-jobs`` scheduler state, ``services`` ``list`` for Holmes discovery, ``namespaces``
``get`` for ``NAMESPACE_DATA_MODE=namespaced``) and a RoleBinding yourself. In that setup also set
the environment variables from the table above yourself via ``runner.additional_env_vars`` — the
presets come from ``runner.rbac.namespaceScoped``, which you may still enable together with a
custom service account.

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

    SA=system:serviceaccount:robusta:robusta-runner-service-account

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
"configmaps"`` — the runner's service account has no ``configmaps get`` in its namespace. With
``runner.rbac.namespaceScoped: true`` and the chart-created service account this cannot happen; it
means a bring-your-own RoleBinding is not matching the pod's service account. This error is fatal
(the runner restarts in a loop until fixed). Check, in the installation namespace:

.. code-block:: bash

    NS=robusta   # your namespace
    SA=robusta-runner-service-account   # your service account name

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
``enabledManagedConfiguration: false``, or grant the ``prometheusrules`` rule via
``runner.customClusterRoleRules`` as shown above. This error is not fatal, but it repeats every
sync cycle.

Related guides
--------------

- :ref:`Read-Only Service Account <read-only-service-account>` — keep cluster-wide read access but
  remove all write permissions.
- :ref:`RBAC: Namespace-Scoped HolmesGPT <rbac-namespace-scoping>` — the equivalent setup for
  HolmesGPT.
