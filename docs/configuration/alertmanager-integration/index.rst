:hide-toc:



Integrating with Prometheus
================================
.. toctree::
   :hidden:
   :maxdepth: 1

   alert-manager
   outofcluster-prometheus
   azure-managed-prometheus
   eks-managed-prometheus
   coralogix_managed_prometheus
   victoria-metrics
   embedded-prometheus
..    grafana-alert-manager



Robusta can :ref:`enhance Prometheus alerts<Enhanced Prometheus Alerts>`. To set this up, see below.

If you installed Robusta's :ref:`Embedded Prometheus Stack`, no setup necessary.


Setup Instructions
^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3


    .. grid-item-card:: :octicon:`book;1em;` In-cluster Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: alert-manager
        :link-type: doc

        Prometheus, in the same cluster as Robusta

    .. grid-item-card:: :octicon:`book;1em;` Centralized Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: outofcluster-prometheus
        :link-type: doc

        Prometheus, in a different cluster than Robusta

    .. grid-item-card:: :octicon:`book;1em;` Azure Managed Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: azure-managed-prometheus
        :link-type: doc

        Special instructions when using Azure Managed Prometheus

    .. grid-item-card:: :octicon:`book;1em;` EKS Managed Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: eks-managed-prometheus
        :link-type: doc

        Special instructions when using EKS Managed Prometheus

    .. grid-item-card:: :octicon:`book;1em;` Coralogix Managed Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: coralogix_managed_prometheus
        :link-type: doc

        Special instructions when using Coralogix Managed Prometheus

    .. grid-item-card:: :octicon:`book;1em;` Victoria Metrics
        :class-card: sd-bg-light sd-bg-text-light
        :link: victoria-metrics
        :link-type: doc

        Victoria Metrics, in the same cluster as Robusta


    .. grid-item-card:: :octicon:`book;1em;` Embedded Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: embedded-prometheus
        :link-type: doc

        Prometheus, installed as part of Robusta's installation

    .. .. grid-item-card:: :octicon:`book;1em;` Grafana AlertManager
    ..     :class-card: sd-bg-light sd-bg-text-light
    ..     :link: grafana-alert-manager
    ..     :link-type: doc

    ..     Special instructions when using Grafana alerts
