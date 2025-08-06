.. _toolset_prometheus:

Prometheus
=============

By enabling this toolset, HolmesGPT will be able to generate graphs from prometheus metrics as well as help you write and
validate prometheus queries. HolmesGPT can also detect memory leak patterns, CPU throttling, lagging queues, and high
latency issues.

Prior to generating a PromQL query, HolmesGPT tends to list the available metrics. This is done to ensure the metrics used
in PromQL are actually available.

Configuration
-------------

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    .. code-block:: yaml

        holmes:
            toolsets:
                prometheus/metrics:
                    enabled: true
                    config:
                        # see below how to find prometheus_url
                        prometheus_url: http://<prometheus host>:9090 # e.g. http://robusta-kube-prometheus-st-prometheus.default.svc.cluster.local:9090
                        
                        # optional
                        #headers:
                        #    Authorization: "Basic <base_64_encoded_string>"


    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    Add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

        toolsets:
            prometheus/metrics:
                enabled: true
                config:
                    # see below how to find prometheus_url
                    prometheus_url: http://<prometheus host>:9090 # e.g. http://robusta-kube-prometheus-st-prometheus.default.svc.cluster.local:9090
                    
                    # optional
                    #headers:
                    #    Authorization: "Basic <base_64_encoded_string>"

It is also possible to set the ``PROMETHEUS_URL`` environment variable instead of the above ``prometheus_url`` config key.

Advanced configuration
******************************************

Below is the full list of options for this toolset:

.. code-block:: yaml

  prometheus/metrics:
    enabled: true
    config:
      prometheus_url: http://<prometheus host>:9090
      healthcheck: "-/healthy" # default value
      headers:
        Authorization: "Basic <base_64_encoded_string>"
      metrics_labels_time_window_hrs: 48 # default value
      metrics_labels_cache_duration_hrs: 12 # default value
      fetch_labels_with_labels_api: false # default value
      fetch_metadata_with_series_api: false # default value
      tool_calls_return_data: true # default value


- **prometheus_url** A base URL for prometheus. This should include the protocol (e.g. `https`) and the port.
- **healthcheck** Path used for health checking Prometheus or Mimir/Cortex endpoint. It defaults to ``-/healthy`` for Prometheus, use ``/ready`` for Grafana Mimir.
- **headers** Extra headers to pass to all prometheus http requests. Use this to pass authentication. Prometheus `supports basic authentication <https://prometheus.io/docs/guides/basic-auth/>`_.
- **metrics_labels_time_window_hrs** Represents the time window, in hours, over which labels are fetched. This avoids fetching obsolete labels. Set it to ``null`` to let HolmesGPT fetch labels regardless of when they were generated.
- **metrics_labels_cache_duration_hrs** How long are labels cached, in hours. Set it to ``null`` to disable caching.
- **fetch_labels_with_labels_api** Uses prometheus `labels API <https://prometheus.io/docs/prometheus/latest/querying/api/#getting-label-names>`_ to fetch labels instead of the `series API <https://prometheus.io/docs/prometheus/latest/querying/api/#finding-series-by-label-matchers>`_. In some cases setting to True can improve the performance of the toolset, however there will be an increased number of HTTP calls to prometheus. You can experiment with both as they are functionally identical.
- **fetch_metadata_with_series_api** Uses the `series API <https://prometheus.io/docs/prometheus/latest/querying/api/#finding-series-by-label-matchers>`_ instead of the `metadata API <https://prometheus.io/docs/prometheus/latest/querying/api/#querying-metric-metadata>`_. You should only set this value to `true` if the metadata API is disabled or not working. HolmesGPT's ability to select the right metric will be negatively impacted because the series API does not return key metadata like the metrics/series description or their type (gauge, histogram, etc.).
- **tool_calls_return_data** Defaults to ``true``. If ``false``, no prometheus data will be returned to HolmesGPT. Set it to ``false`` if you frequently reach the token limit when using this toolset. Setting this setting to ``false`` will also disable HolmesGPT's ability to analyze prometheus data.

Finding the prometheus URL
******************************************

The best way to find the prometheus URL is to use "ask holmes". This only works if your cluster is live and already connected to Robusta.

If not, you can often find the prometheus URL by running the following command (several results may be shown - pick the best match):

.. code-block:: bash

    kubectl get svc --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"."}{.metadata.namespace}{".svc.cluster.local:"}{.spec.ports[0].port}{"\n"}{end}' | grep prometheus | grep -Ev 'operat|alertmanager|node|coredns|kubelet|kube-scheduler|etcd|controller' | awk '{print "http://"$1}'

Capabilities
-----------------
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


Grafana Cloud (Mimir) Configuration
******************************************

To configure Grafana Cloud's Mimir endpoint with HolmesGPT:

1. Create a service account token in Grafana Cloud:

   - Go to **Administration → Service accounts**
   - Create a new service account
   - Generate a service account token (starts with ``glsa_``)

2. Find your Prometheus datasource UID:

   .. code-block:: bash

      curl -H "Authorization: Bearer YOUR_GLSA_TOKEN" \
        "https://YOUR-INSTANCE.grafana.net/api/datasources" | jq

   Look for the UID of your Prometheus datasource (typically ``grafanacloud-prom``).

3. Add the following configuration to your ``generated_values.yaml``:

   .. code-block:: yaml

      holmes:
        toolsets:
          prometheus/metrics:
            enabled: true
            config:
              prometheus_url: https://YOUR-INSTANCE.grafana.net/api/datasources/proxy/uid/PROMETHEUS_DATASOURCE_UID
              fetch_labels_with_labels_api: false  # Important for Mimir
              fetch_metadata_with_series_api: true  # Important for Mimir
              headers:
                Authorization: Bearer YOUR_GLSA_TOKEN

.. note::

   The proxy endpoint URL format (``/api/datasources/proxy/uid/``) is crucial for Grafana Cloud integration as it handles authentication and routing to Mimir automatically.

For complete Grafana Cloud integration including Robusta Runner configuration, see :doc:`/configuration/alertmanager-integration/grafana-cloud-mimir`.

Coralogix Prometheus Configuration
******************************************

To configure Coralogix PromQL endpoint with HolmesGPT:

1. Go to `Coralogix Documentation <https://coralogix.com/docs/integrations/coralogix-endpoints/#promql>`_ and choose the relevant *PromQL Endpoint* for your region.

2. On the Coralogix site, go to **Data Flow → API Keys** and create an API key with permissions to query metrics.

3. Create a Kubernetes secret for the API key and expose it as an environment variable in `generated_values.yaml`:

.. code-block:: yaml

  holmes:
    additionalEnvVars:
    - name: CORALOGIX_API_KEY
      valueFrom:
        secretKeyRef:
          name: coralogix-api-key
          key: CORALOGIX_API_KEY

4. Add the following under your toolsets in the Helm chart:

.. code-block:: yaml

  holmes:
    toolsets:
      prometheus/metrics:
        enabled: true
        config:
          healthcheck: "/api/v1/query?query=up"  # <- this is important
          prometheus_url: "https://prom-api.eu2.coralogix.com"  # change according to your region
          # prometheus_additional_labels: # if you have individual labels for each cluster
          #   cluster: 'CLUSTER_NAME_HERE'
          headers:
            token: "{{ env.CORALOGIX_API_KEY }}"
          metrics_labels_time_window_hrs: 72
          metrics_labels_cache_duration_hrs: 12
          fetch_labels_with_labels_api: true
          tool_calls_return_data: true
          fetch_metadata_with_series_api: true
