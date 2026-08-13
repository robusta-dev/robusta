.. _runner-least-privilege:

Runner Permissions and Least Privilege
========================================

The Robusta runner needs to *read* Kubernetes resources in every namespace — that is how it
discovers workloads, correlates alerts and enriches findings. It also needs to *write* to some
resources, both in its own namespace (to run KRR, Popeye and debug pods) and, for remediation
actions, in the namespaces of the workloads it fixes.

This page explains exactly which permissions the chart grants, and how to reduce the write
permissions granted outside Robusta's own namespace.

What the chart creates
----------------------

.. list-table::
   :header-rows: 1
   :widths: 22 33 45

   * - Kind
     - Name
     - Contains
   * - ClusterRole
     - ``<release>-runner-cluster-role``
     - Cluster-wide reads (``get``/``list``/``watch``) plus the writes that remediation actions
       need in *other* namespaces
   * - Role
     - ``<release>-runner-role``
     - Writes Robusta only performs in its **own** namespace: KRR/Popeye/kubectl jobs, debug pods,
       job secrets, scheduled-job state ConfigMaps, managed ``PrometheusRules``
   * - ClusterRoleBinding
     - ``<release>-runner-cluster-role-binding``
     - Binds the ClusterRole cluster-wide
   * - RoleBinding
     - ``<release>-runner-role-binding``
     - Binds the Role inside the release namespace only

The split matters because a ``ClusterRole`` bound with a ``ClusterRoleBinding`` applies to **every**
namespace. A verb such as ``create secrets`` or ``create deployments`` in that ClusterRole is not
"Robusta can create its own resources" — it is "Robusta can create a Deployment with an arbitrary
pod spec in ``kube-system``", which is equivalent to cluster-admin. Those verbs therefore live in
the namespaced Role, which structurally cannot reach other namespaces.

.. _runner-cluster-wide-write-access:

Reducing cluster-wide writes
----------------------------

Set ``runner.clusterWideWriteAccess: false`` to remove **every** write verb from the runner's
ClusterRole. The ClusterRole then grants only ``get``, ``list`` and ``watch`` — and no ``pods/exec``
at all — while the write verbs are added to the namespaced Role instead, so remediation still works
inside the Robusta namespace:

.. code-block:: yaml

    runner:
      clusterWideWriteAccess: false

Robusta's own features are unaffected: KRR, Popeye, ``kubectl`` enrichments, the Python/Java
debugger pods, node bash, scheduled jobs and managed alerts all operate in the release namespace.

.. note::

   On OpenShift (``openshift.enabled: true``) the chart still grants the OpenShift-specific rules
   cluster-wide — ``use`` on the SecurityContextConstraint the runner pod needs, plus the
   ``apps.openshift.io`` and ``monitoring.coreos.com`` rules required to integrate with OpenShift's
   built-in monitoring stack. Use ``runner.overrideClusterRoles`` if you need to remove those too.

What stops working
^^^^^^^^^^^^^^^^^^

Any action that modifies a resource in **another** namespace, or a cluster-scoped resource:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Action
     - Needs
   * - ``cordon`` / ``uncordon`` / ``drain_node``
     - ``patch nodes``, ``create pods/eviction``
   * - ``rollout_restart`` / ``restart_named_rollout``
     - ``patch deployments``/``statefulsets``/``daemonsets``
   * - ``delete_pod`` and other pod remediation
     - ``delete pods``
   * - ``pod_bash_enricher``, ``volume_analysis``
     - ``get``/``create pods/exec``, ``create pods``
   * - ``scale_hpa_callback``
     - ``patch``/``update horizontalpodautoscalers``
   * - ``job_restart_on_oomkilled_community``
     - ``create``/``delete jobs``
   * - ``create_pvc_snapshot``
     - ``create volumesnapshots``
   * - ``disk_benchmark`` outside the Robusta namespace
     - ``create``/``delete persistentvolumeclaims``

These actions fail with a Kubernetes ``Forbidden`` error; nothing else is affected. If you use only
some of them, keep ``clusterWideWriteAccess: true`` and remove the rest with
``runner.overrideClusterRoles`` (below).

Verifying
^^^^^^^^^

.. code-block:: bash

    SA=system:serviceaccount:<release-namespace>:robusta-runner-service-account

    kubectl auth can-i list pods          --as=$SA -n default   # -> yes  (reads stay cluster-wide)
    kubectl auth can-i create secrets     --as=$SA -n default   # -> no
    kubectl auth can-i create deployments --as=$SA -n kube-system  # -> no
    kubectl auth can-i create jobs        --as=$SA -n <release-namespace>  # -> yes (KRR / Popeye)

    # with clusterWideWriteAccess: false
    kubectl auth can-i create pods/exec   --as=$SA -n default   # -> no
    kubectl auth can-i get pods/exec      --as=$SA -n default   # -> no

.. note::

   Check **both** ``get`` and ``create`` on ``pods/exec``. ``kubectl exec`` sends a POST, which RBAC
   maps to ``create``, but the Kubernetes python client (which Robusta uses) opens the exec stream
   with a GET, which RBAC maps to ``get``. A ClusterRole that grants only ``get`` on ``pods/exec``
   still allows running commands in every pod in the cluster.

Full control with ``overrideClusterRoles``
------------------------------------------

``runner.overrideClusterRoles`` replaces the built-in ClusterRole rules entirely. When it is set the
chart also **skips the namespaced Role and RoleBinding**, so the rules you provide are the only
permissions the runner has. Use it when you need an exact rule set — for example
:ref:`a fully read-only runner <read-only-service-account>`.

``runner.customClusterRoleRules`` is the opposite: those rules are *added* to the built-in
ClusterRole (used for :ref:`Custom Resource Definitions (CRDs) Monitoring`), so it cannot be used to
reduce permissions.

Choosing between the options
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Goal
     - Setting
     - Result
   * - Default
     - —
     - Cluster-wide reads and remediation; Robusta's own writes are namespaced
   * - No writes outside Robusta's namespace
     - ``runner.clusterWideWriteAccess: false``
     - Remediation only inside the release namespace; all Robusta features that stay in their own
       namespace keep working
   * - No writes at all
     - ``runner.overrideClusterRoles``
     - :ref:`Read-only runner <read-only-service-account>`; no Role is created
