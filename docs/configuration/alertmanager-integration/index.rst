:hide-toc:



Integrating with Prometheus
================================
.. toctree::
   :hidden:
   :maxdepth: 1

   alert-manager
   outofcluster-prometheus
   azure-managed-prometheus
   embedded-prometheus


Follow this guide to configure External Prometheus with Robusta after :ref:`installing it <Integrate with Existing Prometheus>`.

Common Methods
^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`book;1em;` Incluster Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: alert-manager
        :link-type: doc

        Connect Prometheus, AlertManager, Grafana, and others.

    .. grid-item-card:: :octicon:`book;1em;` Out of cluster Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: outofcluster-prometheus
        :link-type: doc

        Configure Prometheus to send alerts to Robusta

    .. grid-item-card:: :octicon:`book;1em;` Azure managed Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: azure-managed-prometheus
        :link-type: doc

        Connect your Prometheus cluster on Azure to work with Robusta.

    .. grid-item-card:: :octicon:`book;1em;` Embedded Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: embedded-prometheus
        :link-type: doc

        Learn how to use Prometheus installed automatically by Robusta.

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

