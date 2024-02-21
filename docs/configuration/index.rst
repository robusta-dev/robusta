:hide-toc:

Integrations Overview
==========================


Robusta can gather data from multiple sources, enrich them and send actionable alerts to many destinations. These integrations with external tools are done using Robusta's Helm values.

Follow these guides after :ref:`installing Robusta <install>`.


.. grid::
    :gutter: 3

    .. grid-item-card:: :octicon:`book;1em;` Data Sources
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/index
        :link-type: doc

        Send data to Robusta from Prometheus, AlertManager, Grafana, Thanos and others.

    .. grid-item-card:: :octicon:`book;1em;` Destinations
        :class-card: sd-bg-light sd-bg-text-light
        :link: configuring-sinks
        :link-type: doc

        Send notifications from Robusta to 15+ integrations like Slack, MS Teams, and Email.


Common Destinations
^^^^^^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`cpu;1em;` Robusta UI
        :class-card: sd-bg-light sd-bg-text-light
        :link: sinks/RobustaUI
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Webhook
        :class-card: sd-bg-light sd-bg-text-light
        :link: sinks/webhook
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Jira
        :class-card: sd-bg-light sd-bg-text-light
        :link: sinks/jira
        :link-type: doc
