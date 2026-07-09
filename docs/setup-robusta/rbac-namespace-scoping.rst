.. _rbac-namespace-scoping:

RBAC: Namespace-Scoped Deployments
========================================

By default, Robusta and HolmesGPT use cluster-wide RBAC: they are granted a ``ClusterRole`` bound with a
``ClusterRoleBinding``, so they can read (and, for the runner, act on) resources in every namespace.

In restricted environments you may want to limit what HolmesGPT can see to a specific set of namespaces.
This guide explains how, how it works under the hood, and what the trade-offs are.

Scoping HolmesGPT to Specific Namespaces
----------------------------------------

Set ``holmes.roleBindingNamespaces`` to the list of namespaces HolmesGPT is allowed to access. Instead of a
cluster-wide ``ClusterRoleBinding``, the chart then creates a namespaced ``RoleBinding`` in each listed
namespace (reusing the same ClusterRole for its rules):

.. code-block:: yaml

    holmes:
      roleBindingNamespaces:
        - default
        - monitoring

When this list is empty (the default), HolmesGPT keeps its cluster-wide binding — existing installs are
unaffected.

Apply it with a Helm upgrade (merge it into your existing values file, or pass it as an extra ``-f`` file):

.. code-block:: bash

    helm upgrade --install robusta robusta/robusta \
      -f generated_values.yaml \
      -n <release-namespace>

You can combine this with a :ref:`read-only runner <read-only-service-account>` in the same values file to
get a fully restricted, audit-only deployment.

How It Works
------------

In Kubernetes RBAC, a ``ClusterRole`` is only a set of permissions ("get/list/watch pods", etc.). On its
own it grants nothing — what determines **where** those permissions apply is the **binding type**, not the
role:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Binding
     - Effective scope
   * - ``ClusterRoleBinding`` → ClusterRole
     - Every namespace **plus** cluster-scoped resources (nodes, persistentvolumes, ...)
   * - ``RoleBinding`` (in namespace ``X``) → ClusterRole
     - Only namespaced resources **in namespace** ``X``

A ``RoleBinding`` is allowed to reference a ``ClusterRole``; when it does, Kubernetes applies that
ClusterRole's rules but confined to the RoleBinding's own namespace. HolmesGPT keeps one ClusterRole with
its read rules, and ``roleBindingNamespaces`` only changes how that role is *bound*. For
``roleBindingNamespaces: [default, monitoring]`` the chart renders one ``RoleBinding`` per namespace and no
``ClusterRoleBinding``:

.. code-block:: yaml

    apiVersion: rbac.authorization.k8s.io/v1
    kind: RoleBinding
    metadata:
      name: robusta-holmes-role-binding
      namespace: "default"        # a second identical binding is created in "monitoring"
    roleRef:
      apiGroup: rbac.authorization.k8s.io
      kind: ClusterRole           # reuse the same rules, no duplication
      name: robusta-holmes-cluster-role
    subjects:
      - kind: ServiceAccount
        name: robusta-holmes-service-account
        namespace: robusta        # the ServiceAccount lives in the release namespace

When HolmesGPT's ServiceAccount makes a request, the RBAC authorizer considers all ``ClusterRoleBinding``
objects plus the ``RoleBinding`` objects in the request's namespace. A ``list pods`` in ``default`` matches
the RoleBinding there and is allowed; the same request in ``kube-system`` has no binding and is denied. That
is the entire scoping mechanism — the permission simply does not exist in namespaces where no binding was
created.

.. important::

   - The listed namespaces **must already exist**; the chart does not create them.
   - Access is limited to **namespaced** resources in those namespaces. **Cluster-scoped** resources
     (for example ``nodes``, ``persistentvolumes``, cluster-level events) are no longer granted, because a
     ``RoleBinding`` structurally cannot grant them — only a ``ClusterRoleBinding`` can. Tools that rely on
     them (node health, cluster-wide resource views) will not work in scoped mode.

.. note::

   ``kubectl auth can-i list nodes --as=<holmes-sa> -n default`` may return ``yes`` even though real node
   access is denied. That is a quirk of ``can-i``: passing ``-n default`` evaluates the check *inside* the
   default namespace, where the RoleBinding does grant the ``nodes`` rule, and the authorizer matches
   verb+resource without re-checking that ``nodes`` is cluster-scoped. A real ``kubectl get nodes`` request
   uses an empty namespace, matches no binding, and is denied.

Verifying the Scope
-------------------

.. code-block:: bash

    SA=system:serviceaccount:<release-namespace>:robusta-holmes-service-account

    kubectl auth can-i list pods --as=$SA -n default      # -> yes
    kubectl auth can-i list pods --as=$SA -n monitoring   # -> yes
    kubectl auth can-i list pods --as=$SA -n kube-system  # -> no

Notes on the Runner
-------------------

The Robusta runner remains cluster-wide. To reduce the runner's permissions, use
:ref:`a read-only ClusterRole <read-only-service-account>` via ``runner.overrideClusterRoles``.
Fully scoping the runner to a subset of namespaces is not supported through Helm values, because the
runner watches cluster-wide resources and events to function.
