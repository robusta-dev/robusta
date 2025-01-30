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
   google-managed-prometheus
   victoria-metrics
   grafana-alert-manager
   embedded-prometheus
   troubleshooting-alertmanager
   alert-custom-prometheus



Robusta works best when integrated with Prometheus and AlertManager. When properly setup, Robusta will:

1. Show your existing Prometheus alerts in Robusta, enriched with extra information
2. Fetch relevant metrics from Prometheus and show them on related alerts
3. Fetch metrics from Prometheus and show them in the Robusta UI (optional, only relevant for UI users)

If you installed Robusta's :ref:`Embedded Prometheus Stack`, then everything is pre-integrated and not setup is necessary. If not, you will need follow a guide below.

.. _alertmanager-setup-options:

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

    .. grid-item-card:: :octicon:`book;1em;` Google Managed Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: google-managed-prometheus
        :link-type: doc

        Google Managed Prometheus (GMP)

    .. grid-item-card:: :octicon:`book;1em;` Victoria Metrics
        :class-card: sd-bg-light sd-bg-text-light
        :link: victoria-metrics
        :link-type: doc

        VictoriaMetrics, running in the same K8s cluster as Robusta


    .. grid-item-card:: :octicon:`book;1em;` Grafana AlertManager
        :class-card: sd-bg-light sd-bg-text-light
        :link: grafana-alert-manager
        :link-type: doc

        Special instructions when using Grafana alerts

    .. grid-item-card:: :octicon:`book;1em;` Embedded Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: embedded-prometheus
        :link-type: doc

        All-in-one package of Robusta + kube-prometheus-stack (optional)
