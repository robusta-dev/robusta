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

        Prometheus, running in the same K8s cluster as Robusta

    .. grid-item-card:: :octicon:`book;1em;` Centralized Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: outofcluster-prometheus
        :link-type: doc

        Prometheus, Thanos, Mimir, etc, not running in the same K8s cluster as Robusta

    .. grid-item-card:: :octicon:`book;1em;` Azure Managed Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: azure-managed-prometheus
        :link-type: doc

        Azure Monitor managed service for Prometheus

    .. grid-item-card:: :octicon:`book;1em;` AWS Managed Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: eks-managed-prometheus
        :link-type: doc

        Amazon Managed Service for Prometheus

    .. grid-item-card:: :octicon:`book;1em;` Coralogix
        :class-card: sd-bg-light sd-bg-text-light
        :link: coralogix_managed_prometheus
        :link-type: doc

        Coralogix Managed Prometheus

    .. grid-item-card:: :octicon:`book;1em;` Victoria Metrics
        :class-card: sd-bg-light sd-bg-text-light
        :link: victoria-metrics
        :link-type: doc

        VictoriaMetrics, running in the same K8s cluster as Robusta


    .. grid-item-card:: :octicon:`book;1em;` Embedded Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: embedded-prometheus
        :link-type: doc

        All-in-one package of Robusta + kube-prometheus-stack (optional)

    .. .. grid-item-card:: :octicon:`book;1em;` Grafana AlertManager
    ..     :class-card: sd-bg-light sd-bg-text-light
    ..     :link: grafana-alert-manager
    ..     :link-type: doc

    ..     Special instructions when using Grafana alerts
