Helm
====

By enabling this toolset, HolmesGPT will be able to read access to a cluster's Helm charts and releases.

Configuration
-------------

.. code-block:: yaml

    holmes:
        toolsets:
            helm/core:
                enabled: true
        customClusterRoleRules:
            - apiGroups: [""]
              resources: ["secrets", "pods", "services", "configmaps", "persistentvolumeclaims"]
              verbs: ["get", "list", "watch"]
            - apiGroups: [""]
              resources: ["namespaces"]
              verbs: ["get"]
            - apiGroups: ["apps"]
              resources: ["deployments", "statefulsets", "daemonsets"]
              verbs: ["get", "list", "watch"]
            - apiGroups: ["batch"]
              resources: ["jobs", "cronjobs"]
              verbs: ["get", "list", "watch"]
            - apiGroups: ["networking.k8s.io"]
              resources: ["ingresses"]
              verbs: ["get", "list", "watch"]

.. include:: ./_toolset_configuration.inc.rst

Capabilities
------------
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - helm_list
     - Use to get all the current helm releases
   * - helm_values
     - Use to gather Helm values or any released helm chart
   * - helm_status
     - Check the status of a Helm release
   * - helm_history
     - Get the revision history of a Helm release
   * - helm_manifest
     - Fetch the generated Kubernetes manifest for a Helm release
   * - helm_hooks
     - Get the hooks for a Helm release
   * - helm_chart
     - Show the chart used to create a Helm release
   * - helm_notes
     - Show the notes provided by the Helm chart
