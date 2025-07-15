:hide-toc:

Alert Sources Overview
==========================

Forward alerts from your monitoring system to Robusta for enrichment and automation.

Choose your monitoring system:

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` Prometheus & AlertManager
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/index
        :link-type: doc

        **Most popular** - Works with any Prometheus-compatible stack

    .. grid-item-card:: :octicon:`bell;1em;` Nagios
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/nagios
        :link-type: doc

        **Nagios monitoring** - Forward alerts via webhook

    .. grid-item-card:: :octicon:`bell;1em;` SolarWinds
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/solarwinds
        :link-type: doc

        **SolarWinds monitoring** - Forward alerts via webhook

Don't see your system? Robusta accepts alerts from any system that can send :doc:`HTTP webhooks <../playbook-reference/triggers/webhook>`.
