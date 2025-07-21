:hide-toc:

Alert Sources
=============

Connect your monitoring system to Robusta. When alerts fire, Robusta automatically enriches them with context and applies your automation rules.

**Choose your setup:**

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` Prometheus & AlertManager
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/index
        :link-type: doc

        Standard Prometheus integration. Works with any PromQL-based stack.

    .. grid-item-card:: :octicon:`bell;1em;` Nagios
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/nagios
        :link-type: doc

        Forward Nagios alerts via webhook integration.

    .. grid-item-card:: :octicon:`bell;1em;` SolarWinds
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/solarwinds
        :link-type: doc

        Forward SolarWinds alerts via webhook integration.

**Other systems?** Robusta accepts alerts from any monitoring system via :doc:`HTTP webhooks <exporting/custom-webhooks>`.
