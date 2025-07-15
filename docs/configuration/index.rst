:hide-toc:

Alert Sources Overview
==========================

Connect your existing monitoring systems to Robusta to receive alerts for enrichment, analysis, and automated responses.

Robusta supports alerts from various monitoring platforms through different integration methods:

**Prometheus/AlertManager Integration** - The most common setup, supporting:
- In-cluster and external Prometheus instances
- Managed Prometheus services (AWS, Azure, Google Cloud)
- Prometheus-compatible systems (VictoriaMetrics, Thanos, Mimir)

**Webhook-based Integrations** - For legacy and enterprise monitoring systems:
- Nagios
- SolarWinds
- Any system that can send HTTP webhooks

Getting Started
^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` Prometheus & AlertManager
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/index
        :link-type: doc

        Most popular - comprehensive setup guide for all Prometheus variants

    .. grid-item-card:: :octicon:`bell;1em;` Nagios
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/nagios
        :link-type: doc

        Legacy monitoring systems via webhook integration

    .. grid-item-card:: :octicon:`bell;1em;` SolarWinds
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/solarwinds
        :link-type: doc

        Enterprise monitoring systems via webhook integration
