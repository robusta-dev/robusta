.. _rbac-namespace-scoping:

RBAC: Namespace-Scoped HolmesGPT
========================================

By default, HolmesGPT uses cluster-wide RBAC: the chart creates a ``ClusterRole`` and binds it with a
``ClusterRoleBinding``, so Holmes can read resources in every namespace.

To restrict Holmes to a specific set of namespaces you can create your own ``RoleBinding`` objects that
**reuse the ServiceAccount and ClusterRole the chart already creates**, and remove the cluster-wide binding.
You do not need to create a ServiceAccount or ClusterRole yourself.

What the chart already creates
------------------------------

With the default values, the Holmes chart creates these objects (``<release>`` is your Helm release name,
usually ``robusta``, in the release namespace):

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Kind
     - Name
     - Purpose
   * - ServiceAccount
     - ``<release>-holmes-service-account``
     - Identity the Holmes pod runs as
   * - ClusterRole
     - ``<release>-holmes-cluster-role``
     - The read permissions Holmes needs (rules only)
   * - ClusterRoleBinding
     - ``<release>-holmes-cluster-role-binding``
     - Grants the ClusterRole **cluster-wide** — this is what makes Holmes see every namespace

Reuse the ServiceAccount and ClusterRole; replace the binding
-------------------------------------------------------------

Step 1 — Create a ``RoleBinding`` in each namespace Holmes should access. It binds the **existing**
ServiceAccount to the **existing** ClusterRole, but a ``RoleBinding`` only grants those rules inside its own
namespace:

.. code-block:: yaml

    # holmes-rolebindings.yaml  (one RoleBinding per target namespace)
    apiVersion: rbac.authorization.k8s.io/v1
    kind: RoleBinding
    metadata:
      name: holmes-namespace-scoped
      namespace: default                      # repeat this file for "monitoring", etc.
    roleRef:
      apiGroup: rbac.authorization.k8s.io
      kind: ClusterRole                        # reuse the chart's ClusterRole (rules only)
      name: robusta-holmes-cluster-role
    subjects:
      - kind: ServiceAccount
        name: robusta-holmes-service-account   # reuse the chart's ServiceAccount
        namespace: <release-namespace>

.. code-block:: bash

    kubectl apply -f holmes-rolebindings.yaml

Step 2 — Remove the cluster-wide binding, otherwise it still grants Holmes access to every namespace and the
RoleBindings above are redundant:

.. code-block:: bash

    kubectl delete clusterrolebinding robusta-holmes-cluster-role-binding

Holmes now has read access only in the namespaces where you created a RoleBinding.

.. warning::

   A ``helm upgrade`` re-creates ``robusta-holmes-cluster-role-binding`` (the chart always renders it),
   which restores cluster-wide access. After each upgrade, re-run the ``kubectl delete`` above, or manage
   the deletion/RoleBindings through your GitOps/post-render tooling.

How it works
------------

In Kubernetes RBAC a ``ClusterRole`` is only a set of permissions. On its own it grants nothing — the
**binding type** decides where those permissions apply:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Binding
     - Effective scope
   * - ``ClusterRoleBinding`` → ClusterRole
     - Every namespace **plus** cluster-scoped resources (nodes, persistentvolumes, ...)
   * - ``RoleBinding`` (in namespace ``X``) → ClusterRole
     - Only namespaced resources **in namespace** ``X``

A ``RoleBinding`` may reference a ``ClusterRole``; when it does, Kubernetes applies that ClusterRole's rules
but confined to the RoleBinding's own namespace. That is why we can reuse the chart's ClusterRole without
duplicating its rules — one rule set, one thin binding per namespace. When Holmes' ServiceAccount makes a
request, the authorizer checks all ClusterRoleBindings plus the RoleBindings in the request's namespace: a
``list pods`` in ``default`` matches the RoleBinding there and is allowed; the same request in
``kube-system`` matches nothing and is denied.

.. important::

   Access is limited to **namespaced** resources in the bound namespaces. **Cluster-scoped** resources
   (for example ``nodes``, ``persistentvolumes``, cluster-level events) are no longer granted, because a
   ``RoleBinding`` structurally cannot grant them — only a ``ClusterRoleBinding`` can. Tools that rely on
   them (node health, cluster-wide resource views) will not work in scoped mode.

.. note::

   ``kubectl auth can-i list nodes --as=<holmes-sa> -n default`` may return ``yes`` even though real node
   access is denied. Passing ``-n default`` evaluates the check *inside* the default namespace, where the
   RoleBinding grants the ``nodes`` rule, and the authorizer matches verb+resource without re-checking that
   ``nodes`` is cluster-scoped. A real ``kubectl get nodes`` (empty namespace) matches no binding and is denied.

Verifying the scope
-------------------

.. code-block:: bash

    SA=system:serviceaccount:<release-namespace>:robusta-holmes-service-account

    kubectl auth can-i list pods --as=$SA -n default      # -> yes
    kubectl auth can-i list pods --as=$SA -n monitoring   # -> yes
    kubectl auth can-i list pods --as=$SA -n kube-system  # -> no

Tell Holmes which namespaces it can access
-------------------------------------------

Holmes has no way to discover its own RBAC scope. A denial only ever names the resource and namespace that
were **rejected** ("...cannot list resource pods ... in the namespace kube-system"); it never lists the
namespaces that are **allowed**. Without guidance, Holmes may assume it has cluster-wide access, repeatedly
retry cluster-wide queries (``kubectl get pods -A``, ``get nodes``), or mistake the ``Forbidden`` errors for
a broken cluster.

After scoping, add a **global instruction** telling Holmes exactly which namespaces it may use. Global
instructions are account-level and are injected into Holmes' system prompt for every investigation; set them
in the Robusta UI (HolmesGPT settings → global instructions). Keep the list in sync with the namespaces you
bound above.

Example global instruction:

.. code-block:: text

    This HolmesGPT instance has namespace-scoped RBAC. You can only read Kubernetes resources in the
    "default" and "monitoring" namespaces. Always scope kubectl queries with `-n default` or `-n monitoring`.
    Do not run cluster-wide queries such as `kubectl get pods -A`, `kubectl get nodes`, or
    `kubectl get namespaces` — they will be denied. If something you need is in another namespace, report
    that it is outside your permitted scope instead of retrying.

Notes on the runner
-------------------

The Robusta runner remains cluster-wide. To reduce the runner's permissions, use
:ref:`a read-only ClusterRole <read-only-service-account>` via ``runner.overrideClusterRoles``.
Fully scoping the runner to a subset of namespaces is not supported, because the runner watches
cluster-wide resources and events to function.
