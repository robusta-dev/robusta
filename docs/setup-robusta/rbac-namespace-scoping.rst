.. _rbac-namespace-scoping:

RBAC: Namespace-Scoped Deployments
========================================

By default, Robusta uses cluster-wide RBAC. This guide explains namespace-scoped options and limitations.

Pattern 1: Namespace-Scoped ServiceAccount with Cluster-Wide Role
------------------------------------------------------------------

Deploy Robusta in a specific namespace but monitor the entire cluster.

Pattern 2: Multiple Runners Per Namespace
------------------------------------------

Deploy separate Robusta instances for different teams using namespace-scoped Roles.

Recommendations
---------------

- Use Pattern 1 for cluster-wide visibility with namespace isolation
- Use Pattern 2 for strict multi-tenancy
- Test thoroughly to verify investigations work in your scope
