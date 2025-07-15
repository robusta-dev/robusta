:hide-toc:

Integrations Overview
==========================

Robusta connects to your existing monitoring infrastructure to receive alerts and enrich them with AI analysis and automated responses.

Key Integration Categories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. grid::
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` Alert Sources
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/index
        :link-type: doc

        Connect monitoring systems like Prometheus, Nagios, and SolarWinds to forward alerts to Robusta.

    .. grid-item-card:: :octicon:`brain;1em;` AI Analysis
        :class-card: sd-bg-light sd-bg-text-light
        :link: holmesgpt/index
        :link-type: doc

        Automatically investigate alerts using Holmes GPT with access to logs, metrics, and Kubernetes context.

    .. grid-item-card:: :octicon:`tools;1em;` Additional Tools
        :class-card: sd-bg-light sd-bg-text-light
        :link: resource-recommender
        :link-type: doc

        Extend Robusta with cost optimization (KRR) and cluster misconfiguration detection.

Popular Alert Sources
^^^^^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/alert-manager
        :link-type: doc

        Most popular - works with any Prometheus setup

    .. grid-item-card:: :octicon:`bell;1em;` Nagios
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/nagios
        :link-type: doc

        Legacy monitoring systems via webhook

    .. grid-item-card:: :octicon:`bell;1em;` SolarWinds
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/solarwinds
        :link-type: doc

        Enterprise monitoring systems via webhook
