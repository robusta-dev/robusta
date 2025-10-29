=============================================
Custom Resource Definitions (CRDs) Monitoring
=============================================

Overview
--------

The CRDs monitoring feature enables you to view and manage Custom Resource Definitions and their instances directly from the Robusta UI. This powerful feature provides visibility into:

* All CRDs deployed in your clusters
* Individual CR (Custom Resource) instances and their status
* Resource events and history
* Full YAML manifests
* Detailed resource descriptions

Prerequisites
-------------

To enable CRD monitoring, the Robusta agent needs appropriate permissions to read custom resources in your cluster. This requires adding cluster role rules to your Robusta configuration.

Configuration
-------------

Basic Configuration
^^^^^^^^^^^^^^^^^^^

To enable CRD monitoring, add the ``customClusterRoleRules`` section to your Robusta Helm values:

.. code-block:: yaml

    customClusterRoleRules:
      - apiGroups:
          - "*"
        resources:
          - "*"
        verbs:
          - "list"
          - "get"
          - "watch"

.. warning::
    The above configuration grants read access to all resources. For production environments, it's recommended to limit access to specific CRDs only.

Specific CRD Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

For better security, specify only the CRDs you need to monitor:

**Example 1: Monitoring Cert-Manager Resources**

.. code-block:: yaml

    customClusterRoleRules:
      - apiGroups:
          - "cert-manager.io"
        resources:
          - "certificates"
          - "certificaterequests"
          - "issuers"
          - "clusterissuers"
        verbs:
          - "list"
          - "get"
      - apiGroups:
          - "acme.cert-manager.io"
        resources:
          - "challenges"
          - "orders"
        verbs:
          - "list"
          - "get"

Applying the Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Update your ``values.yaml`` file with the desired configuration
2. Apply the changes using Helm:

.. code-block:: bash

    helm upgrade robusta robusta/robusta \
      --values values.yaml \
      --namespace robusta \
      --reuse-values

Automatic Configuration with Holmes AI
---------------------------------------

Instead of manually configuring permissions for each CRD, you can use Holmes AI to automatically generate the configuration for all CRDs in your cluster.

Using Holmes to Generate Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Navigate to the **Holmes Ask** page in the Robusta UI
2. Use the following prompt:

.. code-block:: text

    I want to add read only cluster roles for all the crds in my cluster.
    This is the format for adding one:
    customClusterRoleRules:
      - apiGroups:
          - "storage.k8s.io"
        resources:
          - "storageclasses"
        verbs:
          - "list"
          - "get"
    Prepare my config

3. Holmes will analyze your cluster and generate a complete configuration including all CRDs
4. Copy the generated configuration and add it to your ``values.yaml``
5. Apply the configuration using Helm as described above

.. tip::
    After Holmes generates the configuration, you can review and modify it to remove any CRDs you don't want to monitor before applying it.

Troubleshooting
---------------

Common Issues and Solutions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Issue 1: CRDs not appearing in UI**

* **Check permissions**: Verify the ClusterRole has the correct permissions

  .. code-block:: bash

      kubectl get clusterrole robusta-runner -o yaml

* **Check agent logs**: Look for permission errors

  .. code-block:: bash

      kubectl logs -n robusta deployment/robusta-runner | grep -i "forbidden"

**Issue 2: "Forbidden" errors when accessing CRDs**

* **Solution**: Add the specific apiGroup and resource to ``customClusterRoleRules``
* **Example error**: ``cannot get resource "certificates" in API group "cert-manager.io"``
* **Fix**: Add the cert-manager.io apiGroup with certificates resource

