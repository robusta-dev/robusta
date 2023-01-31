Install with ArgoCD
#################################

This tutorial installs Robusta with `ArgoCD <https://argoproj.github.io/cd>`_.

Prerequisites
---------------------
* A Kubernetes cluster with ArgoCD
* A ``generated_values.yaml`` file. Follow the :ref:`Quick Install` tutorials to generate this.

.. include:: ../_questions.rst

Preparing Robusta's config
-----------------------------------

Prepare your ``generated_values.yaml`` file for ArgoCD:

* If it's not already present, add ``clusterName: <YOUR-CLUSTER-NAME>``
* If installing on a test cluster like KIND, add ``isSmallCluster: true``

Example ``generated_values.yaml``:

.. code-block:: yaml
    
    clusterName: my_cluster_name # <- This is the line to be added
    isSmallCluster: false        # <- Optional. Set this on test clusters to lower Robusta's resource usage.
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


Configure ArgoCD
--------------------------------

Create a ``NEW APP`` in ArgoCD and fill in the following settings.

``General`` settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Application name:** Your choice (e.g "robusta")
- **Project name:** Your choice (e.g "default")
- **Sync Policy:** Your choice (we recommend starting with ``Manual``)

``Source`` settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Repository URL:** https://robusta-charts.storage.googleapis.com
- **Chart:** robusta
- Change the dropdown box from "GIT" to "HELM"
- **Version:** Choose the latest stable robusta version. (``-alpha`` versions are not recommended.)

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
