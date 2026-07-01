.. _rbac-namespace-scoping:

RBAC: Namespace-Scoped Deployments
========================================

By default, Robusta and HolmesGPT use cluster-wide RBAC: they are granted a ``ClusterRole`` bound with a
``ClusterRoleBinding``, so they can read (and, for the runner, act on) resources in every namespace.

In restricted environments you may want to limit what HolmesGPT can see to a specific set of namespaces.
This guide explains how, and what the trade-offs are.

Scoping HolmesGPT to Specific Namespaces
----------------------------------------

Set ``holmes.overrideClusterRoles`` to the list of namespaces HolmesGPT is allowed to access. Instead of a
cluster-wide ``ClusterRoleBinding``, the chart then creates a namespaced ``RoleBinding`` in each listed
namespace (reusing the same ClusterRole for its rules):

.. code-block:: yaml

    holmes:
      overrideClusterRoles:
        - default
        - monitoring

When this list is empty (the default), HolmesGPT keeps its cluster-wide binding — existing installs are
unaffected.

.. important::

   - The listed namespaces **must already exist**; the chart does not create them.
   - Access is limited to **namespaced** resources in those namespaces. **Cluster-scoped** resources
     (for example ``nodes``, ``persistentvolumes``, cluster-level events) are no longer readable, so
     tools that rely on them (node health, cluster-wide resource views) will not work.

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
