Grafana
=======

Loki
----

By enabling this toolset, HolmesGPT will be able to query logs from `Loki <https://grafana.com/oss/loki/>`_
by proxying through a `Grafana <https://grafana.com/oss/grafana/>`_ instance.

After this toolset is enabled, you can ask Holmes questions like: *Look at my cluster with kubectl, pick an arbitrary node, then fetch logs from loki for that node. Summarize all problems you find.*

Prerequisites
^^^^^^^^^^^^^
A `Grafana service account token <https://grafana.com/docs/grafana/latest/administration/service-accounts/>`_
with the following permissions:

* Basic role -> Viewer
* Data sources -> Reader

Configuration
^^^^^^^^^^^^^

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    Add the following to **Robusta's Helm values:**

    .. code-block:: yaml

        holmes:
          toolsets:
            grafana/loki:
              enabled: true
              config:
                api_key: <your grafana API key>
                url: <your grafana url> # e.g. https://acme-corp.grafana.net 

    .. include:: ./_toolset_configuration.inc.rst

    You can optionally tweak the search terms used by the toolset. This is only needed if your Loki logs settings for pod,
    namespace and node differ from the defaults listed below. To do so, add these search keys to the configuration:

    .. code-block:: yaml

        holmes:
          toolsets:
            grafana/loki:
              enabled: true
              config:
                api_key: <your grafana API key>
                url: <your grafana url> # e.g. https://acme-corp.grafana.net 
                pod_name_search_key: "pod"
                namespace_search_key: "namespace"
                node_name_search_key: "node"

  .. md-tab-item:: Holmes CLI

    Add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

      toolsets:
        grafana/loki:
          enabled: true
          config:
            api_key: <your grafana API key>
            url: https://grafana-url
    
    You can optionally tweak the search terms used by the toolset. This is only needed if your Loki logs settings for pod,
    namespace and node differ from the defaults listed below. To do so, add these search keys to the configuration:

    .. code-block:: yaml

      toolsets:
        grafana/loki:
          enabled: true
          config:
            api_key: <your grafana API key>
            url: https://grafana-url
            pod_name_search_key: "pod"
            namespace_search_key: "namespace"
            node_name_search_key: "node"

Capabilities
^^^^^^^^^^^^

.. include:: ./_toolset_capabilities.inc.rst

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
     - Fetches the Loki logs for a given pod


Tempo
-----

By enabling this toolset, HolmesGPT will be able to fetch trace information from Grafana
Tempo to debug performance related issues, like high latency in your application.

Prerequisites
^^^^^^^^^^^^^
A `Grafana service account token <https://grafana.com/docs/grafana/latest/administration/service-accounts/>`_
with the following permissions:

* Basic role -> Viewer
* Data sources -> Reader

Configuration
^^^^^^^^^^^^^

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chat

    .. code-block:: yaml

      holmes:
        toolsets:
          grafana/tempo:
            enabled: true
            config:
              api_key: <your grafana API key>
              url: https://grafana-url

    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    Add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

      toolsets:
        grafana/tempo:
          enabled: true
          config:
            api_key: <your grafana API key>
            url: https://grafana-url


Capabilities
^^^^^^^^^^^^
.. include:: ./_toolset_capabilities.inc.rst

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


Getting Grafana URL
-----------------------

You can find the Grafana URL required for Loki and Tempo in your Grafana cloud account settings. 

.. image:: /images/grafana-url-for-holmes.png
  :width: 600
  :align: center
