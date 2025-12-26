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

.. image:: /images/crd_demo.png
   :width: 800
   :align: center
   :alt: CRDs monitoring in Robusta UI

Prerequisites
-------------

To enable CRD monitoring, the Robusta agent needs appropriate permissions to read custom resources in your cluster. This requires adding cluster role rules to your Robusta configuration.

Configuration
-------------

Finding CRD Names and API Groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the CRD names and API groups to use in the configuration below:

.. code-block:: bash

    kubectl get crd \
      -o custom-columns=NAME:.spec.names.plural,API_GROUP:.spec.group

This will output something like:

.. code-block:: text

    NAME                      API_GROUP
    alertmanagerconfigs       monitoring.coreos.com
    alertmanagers             monitoring.coreos.com
    imagejobs                 eraser.sh
    imagelists                eraser.sh
    nodenetworkconfigs        acn.azure.com
    overlayextensionconfigs   acn.azure.com
    ...

Basic Configuration
^^^^^^^^^^^^^^^^^^^

Specify read permissions for the CRDs you need to monitor. You can list specific resources or use ``"*"`` to monitor all resources in an API group:

.. code-block:: yaml

    runner:
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

Or to monitor all resources in an API group:

.. code-block:: yaml

    runner:
      customClusterRoleRules:
      - apiGroups:
          - "cert-manager.io"
        resources:
          - "*"
        verbs:
          - "list"
          - "get"

Default CRD Permissions 
^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta includes read-only permissions for common Kubernetes operators and tools by default. These can be individually enabled or disabled:

.. code-block:: yaml

    runner:
      crdPermissions:
        argo: true             # Argo CD, Argo Workflows, Argo Rollouts
        flux: true             # Flux CD (GitOps toolkit)
        kafka: true            # Strimzi Kafka
        keda: true             # KEDA autoscaler
        crossplane: true       # Crossplane
        istio: true            # Istio service mesh
        gatewayApi: true       # Kubernetes Gateway API
        velero: true           # Velero backup/restore
        externalSecrets: true  # External Secrets Operator


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
    runner:
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

