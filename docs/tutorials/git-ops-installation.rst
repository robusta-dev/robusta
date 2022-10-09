GitOps installation (ArgoCD)
##################

Using GitOps tool to manage Kubernetes configuration files in a declarative way is preferred by many Kubernetes users,
as it combines well with Kubernetes principles.

Pre-requisites:

1. Robusta configuration (``generated_values.yaml``), created in :ref:`Installation <Installation>`.

2. A Working setup of `ArgoCD <https://argo-cd.readthedocs.io/en/stable/>`_ or another similar continuous delivery tool for Kubernetes. (We'll assume ArgoCD from now on as it is the most popular)

There are a few options to mange Robusta with ArgoCD.

Directly add the helm charts + values (simplest option)
----

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

.. image:: /images/argo_cd_ui_robusta.png
   :align: center

.. image:: /images/argo_cd_ui_robusta_helm_values.png
   :align: center

- General
    - Application name: Your choice (e.g "robusta")
    - Project name: Your choice (e.g "default")
    - Sync Policy: Your choice (recommended to start with Manual and change it later)
- Source
    - Repository URL: https://robusta-charts.storage.googleapis.com
    - Chart: robusta
    - Change the dropdown box from "GIT" to "HELM"
    - Version: Choose the most stable robusta version, "-alpha" versions are not recommended.
- Destination
    - To install robusta in the same cluster as ArgoCD, use the default https://kubernetes.default.svc option
    - Namespace: Your choice ("default" or "robusta" is recommended)
- Change the "Directory" category to "Helm" by clicking the dropdown box
    - Do **not** use the "values files" option
    - Copy paste the generated_values.yaml file content that you've prepared into the "values" box

Then:
    1. Press the **create** button
    2. Press the **sync** button.
    3. run ``robusta logs`` and make sure there is no error.

.. admonition:: Sync fails
    :class: warning

    On some versions of Robusta, if you set ``enablePrometheusStack: true``, the sync might fail with ``CustomResourceDefinition.apiextensions.k8s.io “prometheuses.monitoring.coreos.com” is invalid: metadata.annotations: Too long: must have at most 262144 bytes``.

    To solve it, use the workaround proposed `here <https://github.com/prometheus-community/helm-charts/issues/1500#issuecomment-1132907207>`_