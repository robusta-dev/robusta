:hide-toc:

Integrating with Prometheus
================================

Follow this guide to configure an external Prometheus with Robusta after :ref:`installing it <Integrate with Existing Prometheus>`.

Common Methods
^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`book;1em;` Incluster Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/alert-manager
        :link-type: doc

        Connect Prometheus, AlertManager, Grafana, and others.

    .. grid-item-card:: :octicon:`book;1em;` Out of cluster Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/outofcluster-prometheus
        :link-type: doc

        Configure Prometheus to send alerts to Robusta

    .. grid-item-card:: :octicon:`book;1em;` Azure managed Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/azure-managed-prometheus
        :link-type: doc

        Connect your Prometheus cluster on Azure to work with Robusta.

.. All Settings
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. All of Robusta's settings are listed as Helm chart values:

.. .. code-block:: yaml

..     helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
..     helm show values robusta/robusta

.. .. admonition:: Avoid using the values.yaml file on GitHub
..     :class: warning

..     It might be tempting to use ``helm/robusta/values.yaml`` in our GitHub repository, but this file wont work.
..     It contains empty placeholders filled in during releases.
