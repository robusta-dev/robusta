:hide-toc:

Overview
================================

The core of Robusta is a rules engine. Rules define how Robusta should enrich, correlate, and respond to incoming events.

Below is an example rule that matches the Prometheus alert ``KubePodCrashLooping``. The rule instructs Robusta to
fetch pod logs and events. Robusta will perform those actions, attach the result to the alert, and then forward the
enriched alert to an external destination like Slack.

An example rule
--------------------

.. grid:: 2
    :margin: 0
    :padding: 0

    .. grid-item::
        :columns: 5

        Rules have the following sections:

        **Triggers**: what events should cause this rule to run?

        **Actions**: what should happen when this rule runs?

        **Sinks**: where should results from this rule be sent?


    .. grid-item::
       :columns: 7

       .. code-block:: yaml

            - triggers:
              - on_prometheus_alert:
                  alert_name: KubePodCrashLooping
              actions:
              - logs_enricher: {}
              - pod_events_enricher: {}

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
