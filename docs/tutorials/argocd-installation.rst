Install with ArgoCD
==============================

This tutorial covers installing Robusta with `ArgoCD <https://argoproj.github.io/cd>`_. You can also install Robusta directly :ref:`with Helm <Install with Helm>`.   

Generate a config
-----------------------------------

Robusta needs some settings to work. For example, if you use Slack then Robusta needs an API key. These settings are configured as Helm values.

We'll generate the Helm values using the ``robusta`` cli tool. There are two ways to install this tool: using ``pip`` or using a Docker container with the ``robusta`` cli already inside. We recommend using pip.

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

            ./robusta version

        .. admonition:: System Requirements
            :class: warning

            A Docker daemon and bash are required.

            On Windows you can use bash inside `WSL <https://docs.microsoft.com/en-us/windows/wsl/install>`_.

You now have a ``generated_values.yaml`` file with a Robusta config. You can customize this more later (for example, to `add integrations <https://docs.robusta.dev/master/catalog/sinks/index.html>`_ like Discord). For now, lets install Robusta and see it in action.

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

Change the value of ``clusterName:`` in ``generated_values.yaml`` file to a new one and use it as your config. Ex: ``clusterName: new_cluster_name``. 


Install
--------------------------------

To setup Robusta with ArgoCD, create a ``NEW APP`` and fill the following:

1. General
    - Application name: Your choice (e.g "robusta")
    - Project name: Your choice (e.g "default")
    - Sync Policy: Your choice (recommended to start with Manual and change it later)
2. Source
    - Repository URL: https://robusta-charts.storage.googleapis.com
    - Chart: robusta
    - Change the dropdown box from "GIT" to "HELM"
    - Version: Choose the most stable robusta version, "-alpha" versions are not recommended.

.. image:: /images/argo_cd_ui_robusta.png
   :align: center

3. Destination
    - To install robusta in the same cluster as ArgoCD, use the default https://kubernetes.default.svc option
    - Namespace: Your choice ("default" or "robusta" is recommended)
4. Change the "Directory" category to "Helm" by clicking the dropdown box
    - Do **not** use the "values files" option
    - Copy paste the generated_values.yaml file content that you've prepared into the "values" box.

.. image:: /images/argo_cd_ui_robusta_helm_values.png
   :align: center

Then:
    1. Press the **create** button.
    2. Choose **all** and press the **sync** button.  
    3. run ``robusta logs`` and make sure there is no error.
.. image:: /images/argocd_sync_all.png
   :align: center

.. admonition:: Sync fails
    :class: warning

    On some versions of Robusta, if you set ``enablePrometheusStack: true``, the sync might fail with ``CustomResourceDefinition.apiextensions.k8s.io “prometheuses.monitoring.coreos.com” is invalid: metadata.annotations: Too long: must have at most 262144 bytes``.

    To solve it, use the workaround proposed `here <https://github.com/prometheus-community/helm-charts/issues/1500#issuecomment-1132907207>`_
