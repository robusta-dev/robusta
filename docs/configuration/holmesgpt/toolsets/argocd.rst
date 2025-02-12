Argocd
======

By enabling this toolset, HolmesGPT will be able to fetch the status, deployment history,
and configuration of ArgoCD applications.

Configuration
-------------

This toolset requires an ``ARGOCD_AUTH_TOKEN`` environment variable as described in
the `argocd documentation <https://argo-cd.readthedocs.io/en/latest/user-guide/commands/argocd_account_generate-token/>`_.

.. code-block:: yaml

    holmes:
        additionalEnvVars:
            - name: ARGOCD_AUTH_TOKEN
              value: <your argocd auth token>
        toolsets:
            argocd/core:
                enabled: true

.. include:: ./_toolset_configuration.inc.rst

Capabilities
------------

.. include:: ./_toolset_capabilities.inc.rst

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
