Generic resource tracking
===============

Track changes to any Kubernetes resource

Track HTTPRoute Change
--------------------------------

For example, get notified when an HTTPRoute resource changes.

**Setup Steps**:

1. **Grant Permissions to Robusta**: By default, Robusta does not have permission to read it
2. **Configure Kubewatch**: Set up Kubewatch to monitor HTTPRoute resources
3. **Create Custom Playbook**: Define notification rules

**1. Grant Permissions to Robusta**

Create a YAML file named ``kubewatch-httproute-permissions.yaml`` with the following content:

.. code-block:: yaml

    kind: ClusterRole
    apiVersion: rbac.authorization.k8s.io/v1
    metadata:
      name: kubewatch-custom-role
    rules:
      - apiGroups:
          - "gateway.networking.k8s.io"
        resources:
          - httproutes
        verbs:
          - get
          - list
          - watch
    ---
    apiVersion: rbac.authorization.k8s.io/v1
    kind: ClusterRoleBinding
    metadata:
      name: kubewatch-custom-role-binding
    roleRef:
      kind: ClusterRole
      name: kubewatch-custom-role
    subjects:
    - kind: ServiceAccount
      name: robusta-forwarder-service-account
      namespace: default

Apply the permissions:

.. code-block:: bash

    kubectl apply -f kubewatch-httproute-permissions.yaml

**2. Configure Kubewatch to Monitor HTTPRoute**

Add the following to the ``kubewatch`` section in your ``generated_values.yaml``:

.. code-block:: yaml

  kubewatch:
    config:
      customresources:
        - group: gateway.networking.k8s.io
          version: v1
          resource: httproutes

**3. Create Custom Playbook**

Add the following to the ``customPlaybooks`` section in your ``generated_values.yaml``:

.. code-block:: yaml

  customPlaybooks:
  - triggers:
    - on_kubernetes_resource_operation:
        namespace_prefix: "monitoring"
        name_prefix: "grafana-"
    actions:
    - create_finding: # 
        title: "resource $name in namespace $namespace was modified"
        aggregation_key: "resource_modified"

Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.
