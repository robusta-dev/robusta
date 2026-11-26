.. _read-only-service-account:

Read-Only Service Account
========================================

By default, Robusta's runner service account is **read-only**: its ClusterRole only grants ``get``, ``list`` and ``watch``. This guide explains what read-only mode means, how to enable specific write access, and how to restrict the read rules further.

Enabling Write Access
---------------------

.. warning::

   These options only exist to support deprecated behaviour. We strongly recommend not enabling them.

Each kind of write access has its own flag under ``runner.rbac``. All flags default to ``false``:

.. code-block:: yaml

    runner:
      rbac:
        enablePodDelete: false               # delete pods
        enableJobDelete: false               # delete Jobs
        enableNodeEdit: false                # cordon and uncordon nodes
        enablePodEvict: false                # evict pods when draining nodes
        enableRobustaConfigMapCreate: false  # create ConfigMaps in Robusta's namespace
        enableRobustaConfigMapEdit: false    # update the scheduled-jobs ConfigMap

The exact Kubernetes permission each flag grants, and where it applies:

.. list-table::
   :widths: 30 20 25 25
   :header-rows: 1

   * - Flag
     - Verb
     - Resource
     - Applies to
   * - ``enablePodDelete``
     - ``delete``
     - ``pods``
     - All namespaces
   * - ``enableJobDelete``
     - ``delete``
     - ``jobs`` (``batch``)
     - All namespaces
   * - ``enableNodeEdit``
     - ``patch``
     - ``nodes``
     - Every node in the cluster
   * - ``enablePodEvict``
     - ``create``
     - ``pods/eviction``
     - All namespaces
   * - ``enableRobustaConfigMapCreate``
     - ``create``
     - ``configmaps``
     - Robusta's namespace only
   * - ``enableRobustaConfigMapEdit``
     - ``get``, ``update``
     - ``configmaps``, the ``scheduled-jobs`` ConfigMap only
     - Robusta's namespace only

``drain`` needs both ``enablePodEvict`` and ``enableNodeEdit``. ``cordon`` and ``uncordon`` need only ``enableNodeEdit``.

With a :ref:`namespace-scoped runner <rbac-namespace-scoped-runner>`, "all namespaces" means Robusta's namespace only, and ``enableNodeEdit`` grants nothing because nodes are not namespaced.

When an action runs without the flag it needs, the runner logs an error that names the flag and links to this page.

``enabledManagedConfiguration`` (default ``false``) grants ``create``, ``update``, ``patch`` and ``delete`` on
PrometheusRules, to sync alerts from the Robusta UI to the cluster, see :ref:`Managed Prometheus Alerts`.

.. _rbac-scheduled-playbooks:

Scheduled Playbooks
-------------------

:ref:`Scheduled playbooks <on_schedule>` are deprecated. We recommend using Kubernetes CronJobs instead.

If you must use the legacy scheduler, you can re-enable it with both ConfigMap flags, but we discourage doing so.
The runner stores the scheduler state in the ``scheduled-jobs`` ConfigMap in its namespace:

.. code-block:: yaml

    runner:
      rbac:
        enableRobustaConfigMapCreate: true
        enableRobustaConfigMapEdit: true

Blocking All Creation
---------------------

Set ``runner.rbac.disableCreateFromServiceAccount: true`` so that Robusta creates nothing in your cluster. This
setting overrides ``enableRobustaConfigMapCreate`` and ``enableRobustaConfigMapEdit``:

- The chart renders no namespaced Role for the runner, even when a ConfigMap flag is enabled
- Scheduled playbooks do not run, and the runner logs an error that names this setting
- The weekly KRR scan :ref:`CronJob <krr-cronjob>` is not created, unless you set ``runner.krrCronJob.enabled: true``

.. code-block:: yaml

    runner:
      rbac:
        disableCreateFromServiceAccount: true

Why Read-Only Mode?
-------------------

Read-only mode is now the recommended way to use Robusta. Several deprecated features in Robusta Classic required
higher level permissions, but they are no longer officially supported. We recommend all users adopt read-only mode.

Restricting Read Rules: Using overrideClusterRoles
--------------------------------------------------

Robusta's Helm chart supports the ``runner.overrideClusterRoles`` parameter. When set, the rules you
provide **fully replace** the built-in runner ClusterRole rules, so only the permissions you list are granted.

.. note::

   Do not confuse this with ``runner.customClusterRoleRules``. That parameter *adds* rules on top of the
   built-in rules, so it **cannot** be used to remove permissions.

   ``overrideClusterRoles`` also replaces the rules added by ``enablePodDelete``, ``enableJobDelete``,
   ``enableNodeEdit`` and ``enablePodEvict``. To use the actions behind these flags, enable the flag and add
   its permission to the override. The two ConfigMap flags are not affected.

To narrow the built-in read rules, create a custom values file with the following configuration:

.. code-block:: yaml

    runner:
      overrideClusterRoles:
        # Core API resources - read-only
        - apiGroups:
            - ""
          resources:
            - daemonsets
            - deployments
            - events
            - namespaces
            - persistentvolumes
            - persistentvolumeclaims
            - pods
            - pods/status
            - pods/log
            - replicasets
            - replicationcontrollers
            - services
            - endpoints
          verbs:
            - get
            - list
            - watch

        # Nodes - read-only
        - apiGroups:
            - ""
          resources:
            - nodes
          verbs:
            - get
            - list
            - watch

        # Apps API - read-only
        - apiGroups:
            - apps
          resources:
            - daemonsets
            - deployments
            - deployments/scale
            - replicasets
            - replicasets/scale
            - statefulsets
          verbs:
            - get
            - list
            - watch

        # Batch API - read-only
        - apiGroups:
            - batch
          resources:
            - cronjobs
            - jobs
          verbs:
            - get
            - list
            - watch

        # Autoscaling - read-only
        - apiGroups:
            - autoscaling
          resources:
            - horizontalpodautoscalers
          verbs:
            - get
            - list
            - watch

        # RBAC - read-only
        - apiGroups:
            - rbac.authorization.k8s.io
          resources:
            - clusterroles
            - clusterrolebindings
            - roles
            - rolebindings
          verbs:
            - get
            - list
            - watch

        # Networking - read-only
        - apiGroups:
            - networking.k8s.io
          resources:
            - ingresses
            - networkpolicies
          verbs:
            - get
            - list
            - watch

        # Events - read-only
        - apiGroups:
            - events.k8s.io
          resources:
            - events
          verbs:
            - get
            - list

        # CRDs - read-only
        - apiGroups:
            - apiextensions.k8s.io
          resources:
            - customresourcedefinitions
          verbs:
            - list
            - get

        # API Registration - read-only
        - apiGroups:
            - apiregistration.k8s.io
          resources:
            - apiservices
          verbs:
            - get
            - list

        # Policy - read-only
        - apiGroups:
            - policy
          resources:
            - poddisruptionbudgets
          verbs:
            - get
            - list

        # Monitoring (optional) - read-only
        - apiGroups:
            - monitoring.coreos.com
          resources:
            - prometheusrules
            - servicemonitors
            - podmonitors
            - alertmanagers
            - silences
          verbs:
            - get
            - list
            - watch

        # Argo CD (optional) - read-only
        - apiGroups:
            - argoproj.io
          resources:
            - applications
            - applicationsets
            - appprojects
            - workflows
            - workflowtemplates
            - cronworkflows
            - rollouts
            - analysisruns
            - analysistemplates
            - experiments
          verbs:
            - get
            - list
            - watch

Then install or upgrade Robusta with this values file:

.. code-block:: bash

    helm upgrade --install robusta robusta/robusta \
      -f generated_values.yaml \
      -f read-only-values.yaml \
      -n robusta-system --create-namespace

Verifying Read-Only Permissions
--------------------------------

After installation, verify that the runner service account has only read permissions. The ClusterRole is
cluster-scoped, so no namespace flag is needed:

.. code-block:: bash

    # Inspect the ClusterRole - the rules should only contain "get", "list", "watch" verbs,
    # and NOT "create", "delete", "patch", or "update".
    kubectl describe clusterrole robusta-runner-cluster-role

Testing Write Protection
------------------------

Use ``kubectl auth can-i`` to confirm what the runner service account can and cannot do
(replace ``robusta-system`` with your release namespace):

.. code-block:: bash

    SA=system:serviceaccount:robusta-system:robusta-runner-service-account

    kubectl auth can-i list pods        --as=$SA -n default   # -> yes
    kubectl auth can-i delete pods      --as=$SA -n default   # -> no
    kubectl auth can-i patch deployments --as=$SA -n default  # -> no
    kubectl auth can-i create pods/exec --as=$SA -n default   # -> no

The read verbs should return ``yes`` while all write/exec verbs return ``no``, confirming the runner is read-only.

Notes and Recommendations
--------------------------

- **CRD Permissions**: If you have custom operators (Argo, Flux, Kafka, KEDA, etc.), add their CRD groups to the read-only rules above with only ``get``, ``list``, ``watch`` verbs
- **Performance**: Read-only mode may improve performance slightly since no write operations are performed
- **Logging**: Monitor Robusta logs for any "permission denied" errors to identify features that require write access
