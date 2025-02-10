Argocd
======

Set of tools to get argocd metadata like list of apps, repositories, projects, etc.

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
    holmes:
        additionalEnvVars:
            - name: ARGOCD_AUTH_TOKEN
              value: <your argocd auth token>
        toolsets:
            argocd/core:
                enabled: true


.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - argocd_app_get
     - Retrieve information about an existing application, such as its status and configuration
   * - argocd_app_diff
     - Display the differences between the current state of an application and the desired state specified in its Git repository
   * - argocd_app_list
     - List the applications in Argocd
   * - argocd_app_history
     - List the deployment history of an application in ArgoCD
   * - argocd_repo_list
     - List all the Git repositories that ArgoCD is currently managing
   * - argocd_proj_list
     - List all available projects
   * - argocd_proj_get
     - Retrieves information about an existing project, such as its applications and policies
   * - argocd_cluster_list
     - List all known clusters
