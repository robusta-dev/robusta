:hide-toc:

Overview
================================

At the core of Robusta is a rules engine which defines how to handle incoming events.

Here is an example rule which takes the Prometheus alert ``KubePodCrashLooping`` and attaches logs and pod events.

.. grid:: 2
    :margin: 0
    :padding: 0

    .. grid-item::
        :columns: 5

        Triggers: this section defines when the alert fires

        Actions: this section defines how Robusta should process the alert.


    .. grid-item::
       :columns: 7

       .. code-block:: yaml

            - triggers:
              - on_prometheus_alert:
                  alert_name: KubePodCrashLooping
              actions:
              - logs_enricher: {}
              - pod_events_enricher: {}

Lets take a concrete ex