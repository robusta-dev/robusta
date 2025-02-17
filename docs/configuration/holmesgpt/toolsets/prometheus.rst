Prometheus
==========

By enabling this toolset, HolmesGPT will be able to analyze prometheus metrics and generate graphs from these metrics.
This gives HolmesGPT the ability to detect memory leak patterns, CPU throttling, high latency for your APIs, etc.

Configuration
-------------


.. code-block:: yaml

    holmes:
        toolsets:
            opensearch/status:
                enabled: true
            config:
                prometheus_url: http://robusta-kube-prometheus-st-prometheus.default.svc.cluster.local:9090

It is also possible to set the ``PROMETHEUS_URL`` environment variable instead of the above ``prometheus_url`` config key.

.. include:: ./_toolset_configuration.inc.rst

Capabilities
------------
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - list_available_metrics
     - List all the available metrics to query from prometheus, including their types (counter, gauge, histogram, summary) and available labels.
   * - execute_prometheus_instant_query
     - Execute an instant PromQL query
   * - execute_prometheus_range_query
     - Execute a PromQL range query
