Install with ArgoCD
#################################

This tutorial installs Robusta with `ArgoCD <https://argoproj.github.io/cd>`_.

Prerequisites
---------------------
* A Kubernetes cluster with ArgoCD
* A ``generated_values.yaml`` file. Follow the :ref:`Generate a Config` tutorial to generate this.

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
.. admonition:: Secrets handling
    :class: note

    Read this guide about :ref:`Managing Secrets`.


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

Configuring Argo Links
-----------------------------------------

For faster Kubernetes troubleshooting, add Robusta links to ArgoCD.

.. image:: /images/argocd_external_urls.png

Add an annotation to each Kubernetes resource with Robusta's URL:

.. code-block::

    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-deployment
      annotations:
        link.argocd.argoproj.io/external-link: "https://platform.robusta.dev/"

Or link applications to their specific Robusta pages:

.. code-block::

    apiVersion: apps/v1
    kind: Deployment #workload type
    metadata:
      name: my-deployment #workload name
      annotations:
        link.argocd.argoproj.io/external-link: "https://platform.robusta.dev/?namespace=%22default%22&type=%22Deployment%22&name=%22some-deployment%22&cluster=%22robusta-cluster-name%22"

.. details:: What is the right Robusta URL for each application?

    It's easiest to open the workload in RobustaUI and copy the URL from the browser.

    You can also build the URL by hand. Edit the above URL, replacing:

    * ``default`` with the workload's namespace
    * ``Deployment`` with the workload type.  Ex: ``StatefulSets``
    * ``some-deployment`` with the workload's name. Ex: ``my-deployment``
    * ``robusta-cluster-name`` with your cluster's name, as defined in the Robusta Helm value ``clusterName``

For more details, refer to the `Argo Documentation on External URLs. <https://argo-cd.readthedocs.io/en/stable/user-guide/external-url/>`_
