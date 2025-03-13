Argocd
======

By enabling this toolset, HolmesGPT will be able to fetch the status, deployment history,
and configuration of ArgoCD applications.

Configuration
-------------

This toolset requires an ``ARGOCD_AUTH_TOKEN`` environment variable. Generate such auth token by following
`these steps <https://argo-cd.readthedocs.io/en/latest/user-guide/commands/argocd_account_generate-token/>`_.
You can consult the `available environment variables <https://argo-cd.readthedocs.io/en/latest/user-guide/environment-variables/>`_
on argocd's official documentation for the CLI.

In addition to the auth token, you will need to tell argocd how to connect to the server. This can be done two ways:

1. **Using port forwarding**. This is the recommended approach if your argocd is inside your Kubernetes cluster.
2. **Setting the env var** ``SERVER_URL``. This is the recommended approach if your argocd is reachable through a public DNS

1. Port forwarding
^^^^^^^^^^^^^^^^^^

This is the recommended approach if your argocd is inside your Kubernetes cluster.

HolmesGPT needs permission to establish a port-forward to ArgoCD. The configuration below includes that authorization.

.. code-block:: yaml

    holmes:
        customClusterRoleRules:
            - apiGroups: [""]
              resources: ["pods/portforward"]
              verbs: ["create"]
        additionalEnvVars:
            - name: ARGOCD_AUTH_TOKEN
              value: <your argocd auth token>
            - name: ARGOCD_OPTS
              value: "--port-forward --port-forward-namespace <your_argocd_namespace> --grpc-web"
        toolsets:
            argocd/core:
                enabled: true
                
.. note::

    Change the namespace ``--port-forward-namespace <your_argocd_namespace>`` to the namespace in which your argocd service
    is deployed.

    The option ``--grpc-web`` in ``ARGOCD_OPTS`` prevents some connection errors from leaking into the tool responses and
    provides a cleaner output for HolmesGPT.

.. include:: ./_toolset_configuration.inc.rst


2. Server URL
^^^^^^^^^^^^^

This is the recommended approach if your argocd is reachable through a public DNS.


.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    .. code-block:: yaml

        holmes:
            additionalEnvVars:
                - name: ARGOCD_AUTH_TOKEN
                  value: <your argocd auth token>
                - name: ARGOCD_SERVER
                  value: argocd.example.com
            toolsets:
                argocd/core:
                    enabled: true

    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    First create the `ARGOCD_AUTH_TOKEN` environment variable:

    .. code-block:: shell

      export ARGOCD_AUTH_TOKEN="<your argocd auth token>"
      export ARGOCD_SERVER="argocd.example.com"

    Then add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

          toolsets:
              argocd/core:
                  enabled: true

    To test, run: 

    .. code-block:: yaml
      
        holmes ask "Which argocd applications are failing and why?"

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
