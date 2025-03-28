.. _toolset_prometheus:

Prometheus
==========

By enabling this toolset, HolmesGPT will be able to generate graphs from prometheus metrics as well as help you write and
validate prometheus queries. HolmesGPT can also detect memory leak patterns, CPU throttling, lagging queues, and high
latency issues.

Prior to generating a PromQL query, HolmesQPT tends to list the available metrics. This is done to ensure the metrics used
in PromQL are actually available.

Configuration
-------------

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chat

    .. code-block:: yaml

        holmes:
            toolsets:
                prometheus/metrics:
                    enabled: true
                    config:
                        prometheus_url: http://<prometheus host>:9090
                        headers:
                            Authorization: "Basic <base_64_encoded_string>"


    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    Add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

        toolsets:
            prometheus/metrics:
                enabled: true
                config:
                    prometheus_url: http://<prometheus host>:9090
                    headers:
                        Authorization: "Basic <base_64_encoded_string>"

It is also possible to set the ``PROMETHEUS_URL`` environment variable instead of the above ``prometheus_url`` config key.

**Advanced configuration**

Below is the full list of options for this toolset:

.. code-block:: yaml

  prometheus/metrics:
    enabled: true
    config:
      prometheus_url: http://<prometheus host>:9090
      headers:
        Authorization: "Basic <base_64_encoded_string>"
      metrics_labels_time_window_hrs: 48 # default value
      metrics_labels_cache_duration_hrs: 12 # default value
      fetch_labels_with_labels_api: false # default value
      fetch_metadata_with_series_api: false # default value
      tool_calls_return_data: true # default value


- **prometheus_url** A base URL for prometheus. This should include the protocol (e.g. `https`) and the port.
- **headers** Extra headers to pass to all prometheus http requests. Use this to pass authentication. Prometheus `supports basic authentication <https://prometheus.io/docs/guides/basic-auth/>`_.
- **metrics_labels_time_window_hrs** Represents the time window, in hours, over which labels are fetched. This avoids fetching obsolete labels. Set it to ``null`` to let HolmesGPT fetch labels regardless of when they were generated.
- **metrics_labels_cache_duration_hrs** How long are labels cached, in hours. Set it to ``null`` to disable caching.
- **fetch_labels_with_labels_api** Uses prometheus `labels API <https://prometheus.io/docs/prometheus/latest/querying/api/#getting-label-names>`_ to fetch labels instead of the `series API <https://prometheus.io/docs/prometheus/latest/querying/api/#finding-series-by-label-matchers>`_. In some cases setting to True can improve the performance of the toolset, however there will be an increased number of HTTP calls to prometheus. You can experiment with both as they are functionally identical.
- **fetch_metadata_with_series_api** Uses the `series API <https://prometheus.io/docs/prometheus/latest/querying/api/#finding-series-by-label-matchers>`_ instead of the `metadata API <https://prometheus.io/docs/prometheus/latest/querying/api/#querying-metric-metadata>`_. You should only set this value to `true` if the metadata API is disabled or not working. HolmesGPT's ability to select the right metric will be negatively impacted because the series API does not return key metadata like the metrics/series description or their type (gauge, histogram, etc.).
- **tool_calls_return_data** Defaults to ``true``. If ``false``, no prometheus data will be returned to HolmesGPT. Set it to ``false`` if you frequently reach the token limit when using this toolset. Setting this setting to ``false`` will also disable HolmesGPT's ability to analyze prometheus data.

**Finding the prometheus URL**

The best way to find the prometheus URL is to use "ask holmes". This only works if your cluster is live and already connected to Robusta.

If not, follow these steps:

1. Run ``kubectl get services -n <monitoring-namespace>`` to list all services. Replace ``<monitoring-namespace>`` with the namespace where Prometheus is deployed. This is often ``monitoring`` or ``prometheus``. You can also run ``kubectl get services -A`` which will list all services in all namespaces.
2. Identify which are the namespace and name of your Prometheus service. You can set up port forwarding to test if the service is correct and if Prometheus is reachable.
3. Run ``kubectl describe service <service-name> -n <namespace>`` to get details about the service, including the cluster IP and port.
4. Set the DNS or the cluster IP as well as the port to the configuration field ``prometheus_url`` as mentioned above.


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
