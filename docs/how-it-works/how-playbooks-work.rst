How Rules Work
================================

How Automations Work
----------------------

Every automation has three parts:

.. grid:: 1 1 2 3

    .. grid-item-card:: Triggers
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../configuration/triggers/index
        :link-type: doc

        When to run
        (on alerts, logs, changes, etc)

    .. grid-item-card::  Actions
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../configuration/actions/index
        :link-type: doc

        What to do
        (over 50 builtin actions)

    .. grid-item-card::  Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../configuration/sinks/index
        :link-type: doc

        Where to send the result
        (Slack, etc)


Rules are pipelines
---------------------------

All events coming into Robusta are matched against ``triggers``.

Any matching events then flow to ``actions``.

Finally, any output from ``actions`` is sent to ``sinks``.

Every event in the pipeline has a type
------------------------------------------------

Each trigger outputs an event of a specific type. Each actions expects an event of a specific type.

For example, ``on_prometheus_alert`` outputs a ``PrometheusAlert`` event. Likewise, ``on_pod_update`` outputs a
``PodChangeEvent``.

These events flow into the ``actions`` section. Each ``action`` requires events of a specific type.
For example, the ``logs_enricher`` action expects to receive events that have a Pod object. This can be a
``PrometheusAlert`` event or a ``PodEvent``.
