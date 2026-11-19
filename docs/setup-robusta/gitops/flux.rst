Install with Flux
#################################

This tutorial installs Robusta with `Flux <https://fluxcd.io/>`_ using Flux `HelmRelease`.

Prerequisites
---------------------
* A Kubernetes cluster with Flux installed.
* A ``generated_values.yaml`` file. Follow the :ref:`Generate a Config` tutorial to generate this.

.. include:: ../_questions.rst


Preparing Robusta's config
-----------------------------------

Prepare your ``generated_values.yaml`` file for Flux:

* If it's not already present, add ``clusterName: <YOUR-CLUSTER-NAME>``
* If installing on a test cluster like KIND, add ``isSmallCluster: true``

Example ``generated_values.yaml``:

.. code-block:: yaml

    clusterName: my_cluster_name # <- This is the line to be added
    globalConfig:
      signing_key: xxxxxx
      account_id: xxxxxx
    sinksConfig:
    - robusta_sink:
        name: robusta_ui_sink
        token: xxxxxx
    enablePrometheusStack: true
    enablePlatformPlaybooks: true
    runner:
      sendAdditionalTelemetry: true

.. admonition:: Don't commit secrets in plain text
    :class: warning

    The ``signing_key``, ``account_id``, and the ``robusta_sink`` ``token`` shown above are
    sensitive. When using GitOps you typically don't want them in your Git repo as plain text.

    See :ref:`Loading Robusta credentials from secrets` for a complete example that loads all three
    from a Kubernetes Secret (compatible with SealedSecrets, External Secrets, Vault, etc.). For
    other sensitive Helm values, see :ref:`Managing Secrets`.


Creating a ``HelmRepository``
--------------------------------
Run the following command to add Robusta Helm chart as a Flux HelmRepository.


.. code-block:: bash

        flux create source helm robusta \
            --url https://robusta-charts.storage.googleapis.com \
            --namespace robusta \
            --export > robusta-helm.yaml

- **--namespace:** Specified namespace should be present in the cluster.


Creating a ``HelmRelease``
----------------------------
Now lets use the HelmRepository to create a HelmRelease of Robusta.


.. code-block:: bash

        flux create helmrelease robusta \
            --namespace robusta \
            --chart=robusta \
            --source=HelmRepository/robusta \
            --chart-version="VERSION" \
            --values=./path/to/generated_values.yaml \
            --export > robusta-release.yaml

- **--chart-version:** Replace **VERSION** with the latest `Robusta release <https://github.com/robusta-dev/robusta/releases>`_.

.. admonition:: Automatic updates
    :class: note

    To automatically upgrade upon a new helm release use ">=VERSION".

Finish installing
--------------------
Move `robusta-helm.yaml` and `robusta-release.yaml` to the Flux bootstrap path.

Commit and push the changes. Wait for the repository to reconcile.
