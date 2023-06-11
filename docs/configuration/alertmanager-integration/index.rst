:hide-toc:



Integrating with Prometheus
================================
.. toctree::
   :hidden:
   :maxdepth: 1

   alert-manager
   outofcluster-prometheus
   kube-prometheus-stack
   azure-managed-prometheus
   victoria-metrics
   embedded-prometheus


Robusta can :ref:`enhance Prometheus alerts<Enhanced Prometheus Alerts>`. To configure this, there are two key steps:

1. Configure a push integration to receive alerts.
2. Configure a pull integration to fetch graphs.

Note: If you installed Robusta's :ref:`Embedded Prometheus Stack`, neither step is necessary. Everything is pre-configured.


Common Methods
^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`book;1em;` Kube Prometheus Stack
        :class-card: sd-bg-light sd-bg-text-light
        :link: kube-prometheus-stack
        :link-type: doc

        For users with an existing Kube Prometheus Stack or Prometheus Operator

    .. grid-item-card:: :octicon:`book;1em;` In-cluster Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: alert-manager
        :link-type: doc

        For users with Prometheus and Robusta installed in the same cluster

    .. grid-item-card:: :octicon:`book;1em;` Out of cluster Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: outofcluster-prometheus
        :link-type: doc

        For users with Prometheus installed on a different cluster than Robusta

    .. grid-item-card:: :octicon:`book;1em;` Azure managed Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: azure-managed-prometheus
        :link-type: doc

        Connect your Prometheus cluster on Azure to work with Robusta.

    .. grid-item-card:: :octicon:`book;1em;` Victoria Metrics
        :class-card: sd-bg-light sd-bg-text-light
        :link: victoria-metrics
        :link-type: doc

        For users using AlertManager with Victoria Metrics

    
    .. grid-item-card:: :octicon:`book;1em;` Embedded Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: embedded-prometheus
        :link-type: doc

        Learn to configure Prometheus already installed by Robusta

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

