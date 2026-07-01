.. _read-only-service-account:

Read-Only Service Account
========================================

By default, Robusta's runner service account has permissions to create, update, and delete Kubernetes resources. This guide explains how to restrict the runner to read-only permissions for environments where you want to prevent any modifications to cluster resources.

Why Read-Only Mode?
-------------------

Read-only mode is useful in scenarios where you want to:

- **Prevent accidental modifications**: Ensure that even if a playbook or investigation logic has a bug, no cluster resources will be modified
- **Comply with security policies**: Meet organizational requirements for read-only access in certain environments
- **Prevent node operations**: Prevent users from draining or restarting nodes through investigations
- **Audit-only mode**: Run Holmes for investigation and diagnostics without remediation capabilities

Limitations of Read-Only Mode
-----------------------------

When using read-only permissions, the following Robusta features will not be available:

- **Auto-remediation**: Playbooks that automatically fix issues (restart pods, scale deployments, drain nodes, etc.)
- **Silence management**: Creating or deleting alert silences
- **Pod debugging**: Live debugging tools that require container execution
- **Resource modification**: Any playbook or action that modifies Kubernetes resources

These features require write permissions and will gracefully fail if attempted with read-only service account.

**Read-only mode is ideal for**: Investigation, diagnostics, log analysis, metric enrichment, and reporting.

Implementation: Using customClusterRoleRules
---------------------------------------------

Robusta's Helm chart supports the ``customClusterRoleRules`` parameter, which allows you to completely replace the default ClusterRole rules with your own custom rules.

To use read-only mode, create a custom values file with the following configuration:

.. code-block:: yaml

    runner:
      customClusterRoleRules:
        # Core API resources - read-only
        - apiGroups:
            - ""
          resources:
            - configmaps
            - daemonsets
            - deployments
            - events
            - namespaces
            - persistentvolumes
            - persistentvolumeclaims
            - pods
            - pods/status
            - pods/exec
            - pods/log
            - replicasets
            - replicationcontrollers
            - services
            - serviceaccounts
            - endpoints
            - secrets
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
            - podsecuritypolicies
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

After installation, verify that the runner service account has only read permissions:

.. code-block:: bash

    # Check the ClusterRole
    kubectl describe clusterrole robusta-runner-cluster-role -n robusta-system

    # Verify that the rules only contain "get", "list", "watch" verbs
    # You should NOT see "create", "delete", "patch", or "update" verbs

Testing Write Protection
------------------------

To confirm that write operations are blocked, try a simple test:

.. code-block:: bash

    # Get the runner pod
    RUNNER_POD=$(kubectl get pod -n robusta-system -l app.kubernetes.io/name=robusta-runner -o jsonpath='{.items[0].metadata.name}')

    # Try to create a test pod (should fail with permission denied)
    kubectl exec -it $RUNNER_POD -n robusta-system -- \
      kubectl create pod test --image=nginx -n default

This command should fail with a "forbidden" or "permission denied" error, confirming that write operations are blocked.

Notes and Recommendations
--------------------------

- **CRD Permissions**: If you have custom operators (Argo, Flux, Kafka, KEDA, etc.), add their CRD groups to the read-only rules above with only ``get``, ``list``, ``watch`` verbs
- **Performance**: Read-only mode may improve performance slightly since no write operations are performed
- **Logging**: Monitor Robusta logs for any "permission denied" errors to identify features that require write access
