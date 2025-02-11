Grafana
====

Loki
------

Fetches kubernetes pods and node logs from Loki

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
    holmes:

        toolsets:
            grafana/loki:
                enabled: true
                config:
                    api_key: <your grafana API key>
                    url: <Grafana's URL>

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - list_loki_datasources
     - Fetches the Loki data sources in Grafana
   * - fetch_loki_logs_by_node
     - Fetches the Loki logs for a given node
   * - fetch_loki_logs_by_label
     - Fetches the Loki logs for a label and value from a Tempo trace
   * - fetch_loki_logs_by_pod


Tempo
------

Fetches kubernetes traces from Tempo

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
    holmes:

        toolsets:
            grafana/tempo:
                enabled: true
                config:
                    api_key: <your grafana API key>
                    url: <Grafana's URL>


.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - list_all_datasources
     - Fetches All the data sources in Grafana
   * - fetch_tempo_traces_by_min_duration
     - Lists Tempo traces ids that exceed a specified minimum duration in a given time range
   * - fetch_tempo_trace_by_id
     - Retrieves detailed information about a Tempo trace using its trace ID. Use this to investigate a trace.
