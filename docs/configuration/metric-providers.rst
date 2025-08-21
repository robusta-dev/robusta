:hide-toc:

General Settings
================

Connect Robusta to your metrics backend to enable advanced features like alert enrichment with historical data, metric queries, and alert silencing. Metric provider integration is optional but highly recommended.


Why Configure a Metric Provider?
--------------------------------

When Robusta has access to your metrics it can help with:

- **Alert Enrichment** - Automatically attach relevant graphs to alerts
- **Historical Context** - Query past data to understand trends
- **Alert Silencing** - Create and manage silences directly from Robusta
- **AI Insights** - Provide HolmesGPT with metrics for better root cause analysis

Supported Providers
-------------------

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`server;1em;` In-cluster Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-in-cluster
        :link-type: doc

        Standard Prometheus running in your Kubernetes cluster

    .. grid-item-card:: :octicon:`globe;1em;` External Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-external
        :link-type: doc

        Prometheus, Thanos, or Mimir outside your cluster

    .. grid-item-card:: :octicon:`organization;1em;` Azure Managed
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-azure
        :link-type: doc

        Azure Monitor managed Prometheus service

    .. grid-item-card:: :octicon:`organization;1em;` AWS Managed
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-aws
        :link-type: doc

        Amazon Managed Prometheus (AMP)

    .. grid-item-card:: :octicon:`organization;1em;` Google Managed
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-google
        :link-type: doc

        Google Cloud Managed Prometheus

    .. grid-item-card:: :octicon:`database;1em;` Coralogix
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-coralogix
        :link-type: doc

        Coralogix managed Prometheus

    .. grid-item-card:: :octicon:`database;1em;` VictoriaMetrics
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-victoria
        :link-type: doc

        VictoriaMetrics time-series database
