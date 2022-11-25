Install with ArgoCD
==============================

This tutorial installs Robusta with `ArgoCD <https://argoproj.github.io/cd>`_. You can also install :ref:`with Helm <Install with Helm>`.

Generate a config
-----------------------------------

Robusta needs settings to work. For example, if you use Slack then Robusta needs an API key. These settings are configured as Helm values.

We'll generate the Helm values using the ``robusta`` cli tool. There are two ways to install this tool: using ``pip`` or using a Docker container with the ``robusta`` cli already inside. We recommend pip.

.. tab-set::    

    .. tab-item:: pip
        :name: pip-cli-tab

        Install the ``robusta`` cli tool with ``pip``:

        .. code-block:: bash
            :name: cb-pip-install

            pip install -U robusta-cli --no-cache

        Run the ``robusta`` cli tool to generate a Helm values file:

        .. code-block:: bash
           :name: cb-robusta-gen-config

            robusta gen-config

        .. admonition:: System Requirements
            :class: warning

            Python 3.7 or higher is required.

            On systems with both Python 2 and Python 3, make sure you run ``pip3``

            You also must have Python's script directory in your PATH. When this is not the case, errors like ``command not found: robusta`` occur. See :ref:`Common Errors` to fix this.

    .. tab-item:: docker
        :name: docker-cli-tab

        Download the robusta script and grant execute permissions:

        .. code-block:: bash
            :name: cb-docker-cli-download

            curl -fsSL -o robusta https://docs.robusta.dev/master/_static/robusta
            chmod +x robusta

        Run the ``robusta`` cli tool to generate a Helm values file:

        .. code-block:: bash
            :name: cb-docker-cli-example

            ./robusta gen-config

        .. admonition:: System Requirements
            :class: warning

            A Docker daemon and bash are required.

            On Windows you can use bash inside `WSL <https://docs.microsoft.com/en-us/windows/wsl/install>`_.


Edit your generated_values.yaml files so it will be ready for ArgoCD, by adding ``clusterName: <YOUR-CLUSTER-NAME>`` at the top, if not already present. Test clusters like Kind and Colima tend to have fewer resources. You can lower the resource usage of Robusta by including ``isSmallCluster: true``. On production it is recommended to leave it as ``isSmallCluster: false``.

Example:

.. code-block:: yaml
    
    clusterName: my_cluster_name # <- This is the line to be added
    isSmallCluster: false #optional & setting this to true lowers the resource requests of Robusta.
    globalConfig:
      signing_key: xxxxxx
      account_id: xxxxxx
    sinksConfig:
    - slack_sink:
        name: main_slack_sink
        slack_channel: robusta-staging-alerts
        api_key: xxxxxx
    - robusta_sink:
        name: robusta_ui_sink
        token: xxxxxx
    enablePrometheusStack: true
    enablePlatformPlaybooks: true
    runner:
      sendAdditionalTelemetry: true
    rsa:
      prv: xxxxxx
      pub: xxxxxx

You now have a ``generated_values.yaml`` file with a Robusta config. You can customize this more later (for example, to `add integrations <https://docs.robusta.dev/master/automation/sinks/index.html>`_ like Discord). For now, lets install Robusta and see it in action.

.. Options
.. ^^^^^^^^^^^^^

.. There are a few options to mange Robusta with ArgoCD.

.. 1. Directly add the ``generated_value.yaml`` to argo cd:
..     - ``generated_values.yaml`` file will be saved directly in ArgoCD

.. 2. Commit your ``generated_value.yaml`` file to git:
..     - A git repo needs to be created to store ``generated_value.yaml`` (or add it to existing one)
..     - You'll have to :ref:`create Kubernetes secrets <Configuration secrets>` for robusta keys
..     - Requires more advanced ArgoCD functions to combine the robusta helm chart with the external ``generated_value.yaml`` file

.. We'll describe the simpler option here. We're currently working on a guide for the more advanced option, contact us if you have questions.


Reuse a config
-------------------
You don't have to create a new ``generated_values.yaml`` everytime you install Robusta on a new cluster. 

Once you've created ``generated_values.yaml`` once, you should use that file for all clusters. Just change the value of ``clusterName`` for each cluster to something descriptive.

Install
--------------------------------

To setup Robusta with ArgoCD, create a ``NEW APP`` and fill in the following settings.

``General`` settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Application name: Your choice (e.g "robusta")
- Project name: Your choice (e.g "default")
- Sync Policy: Your choice (recommended to start with ``Manual``)

``Source`` settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Repository URL: https://robusta-charts.storage.googleapis.com
- Chart: robusta
- Change the dropdown box from "GIT" to "HELM"
- Version: Choose the most stable robusta version, "-alpha" versions are not recommended.

``Destination`` settings
^^^^^^^^^^^^^^^^^^^^^^^^^^

- To install robusta in the same cluster as ArgoCD, use the default https://kubernetes.default.svc option
- Namespace: Your choice ("default" or "robusta" is recommended)

Here is a screenshot of all settings so far:

.. image:: /images/argo_cd_ui_robusta.png
   :align: center


``Directory`` settings
^^^^^^^^^^^^^^^^^^^^^^^

Change the "Directory" category to "Helm" by clicking the dropdown box.

Then paste the contents of ``generated_values.yaml`` into the ``values`` option.

.. warning::

    Make sure you fill in ``values``, not ``values files``

.. image:: /images/argo_cd_ui_robusta_helm_values.png
   :align: center

Finish installing
^^^^^^^^^^^^^^^^^
Click the **create** button. Then choose **all** and press the **sync** button.

Finally, run ``robusta logs`` from your cli and make sure there is no error.

.. image:: /images/argocd_sync_all.png
   :align: center

.. admonition:: Sync fails
    :class: warning

    On some Robusta versions, the sync might fail with ``CustomResourceDefinition.apiextensions.k8s.io “prometheuses.monitoring.coreos.com” is invalid: metadata.annotations: Too long: must have at most 262144 bytes``.

    To solve it, use the workaround proposed `here <https://github.com/prometheus-community/helm-charts/issues/1500#issuecomment-1132907207>`_
