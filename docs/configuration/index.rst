:hide-toc:

Alert Sources
=============

Connect your monitoring system to Robusta, to enrich alerts and apply automation rules.

**Choose your setup:**

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` Prometheus & AlertManager
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/index
        :link-type: doc

        Any Prometheus-compatible stack

    .. grid-item-card:: :octicon:`bell;1em;` Nagios
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/nagios
        :link-type: doc

        Forward Nagios alerts by webhook

    .. grid-item-card:: :octicon:`bell;1em;` NewRelic
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/newrelic
        :link-type: doc

        Forward NewRelic alerts by webhook

    .. grid-item-card:: :octicon:`bell;1em;` SolarWinds
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/solarwinds
        :link-type: doc

        Forward SolarWinds alerts by webhook

**Have alerts elsewhere?** Send alerts via the generic :doc:`HTTP webhook endpoint <exporting/custom-webhooks>`.
