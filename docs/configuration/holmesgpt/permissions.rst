

Adding Permissions for Additional Resources
===========================================

There are scenarios where HolmesGPT may require access to additional Kubernetes resources or CRDs to perform specific analyses or interact with external tools.

You will need to extend its ClusterRole rules whenever HolmesGPT needs to access resources that are not included in its default configuration.

Common Scenarios for Adding Permissions:

* External Integrations and CRDs: When HolmesGPT needs to access custom resources (CRDs) in your cluster, like ArgoCD Application resources or Istio VirtualService resources.
* Additional Kubernetes resources: By default, Holmes can only access a limited number of Kubernetes resources. For example, Holmes has no access to Kubernetes secrets by default. You can give Holmes access to more built-in cluster resources if it is useful for your use case.

As an example, let's consider a case where we ask HolmesGPT to analyze the state of Argo CD applications and projects to troubleshoot issues related to application deployments managed by Argo CD, but it doesn't have access to the relevant CRDs.

**Steps to Add Permissions for Argo CD:**

1. **Update generated_values.yaml with Required Permissions:**

Add the following configuration under the ``customClusterRoleRules`` section:

.. code-block:: yaml

    enableHolmesGPT: true
    holmes:
      customClusterRoleRules:
        - apiGroups: ["argoproj.io"]
          resources: ["applications", "appprojects"]
          verbs: ["get", "list", "watch"]

2. **Apply the Configuration:**

Deploy the updated configuration using Helm:

.. code-block:: bash

  helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

This will grant HolmesGPT the necessary permissions to analyze Argo CD applications and projects.
Now you can ask HolmesGPT questions like "What is the current status of all Argo CD applications in the cluster?" and it will be able to answer.
