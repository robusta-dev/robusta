ArgoCD installation
==============================

Using GitOps tool to manage Kubernetes configuration files in a declarative way is preferred by many Kubernetes users,
as it combines well with Kubernetes principles.

Pre-requisites: 

1. Robusta configuration (``generated_values.yaml``), created in :ref:`Installation <Installation>`.

2. A Working setup of `ArgoCD <https://argo-cd.readthedocs.io/en/stable/>`_ or another similar continuous delivery tool for Kubernetes. (We'll assume ArgoCD from now on as it is the most popular)

Options
^^^^^^^^^^^^^

There are a few options to mange Robusta with ArgoCD.

1. Directly add the ``generated_value.yaml`` to argo cd:
    - ``generated_values.yaml`` file will be saved directly in ArgoCD

2. Commit your ``generated_value.yaml`` file to git:
    - A git repo needs to be created to store ``generated_value.yaml`` (or add it to existing one)
    - You'll have to :ref:`create Kubernetes secrets <Configuration secrets>` for robusta keys
    - Requires more advanced ArgoCD functions to combine the robusta helm chart with the external ``generated_value.yaml`` file

We'll describe the simpler option here. We're currently working on a guide for the more advanced option, contact us if you have questions.

Directly add the helm charts + values (simplest option)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, edit your generated_values.yaml files so it will be ready for ArgoCD, by adding ``clusterName: <YOUR-CLUSTER-NAME>`` at the top, if not already present.
Example:

.. code-block:: yaml

    clusterName: my_cluster_name # <- This is the line to be added
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

To add robusta to ArgoCD, use the instructions `here <https://argo-cd.readthedocs.io/en/stable/getting_started/#creating-apps-via-ui/>`_, and fill the following:

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
