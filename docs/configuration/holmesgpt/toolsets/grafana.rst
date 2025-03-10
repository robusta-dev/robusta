Grafana
=======

Loki
----

By enabling this toolset, HolmesGPT will be able to consult node and pod logs from `Loki <https://grafana.com/oss/loki/>`_
by proxying through a `Grafana <https://grafana.com/oss/grafana/>`_ instance.

In the future this toolset will be able to run any query against Loki logs.

Configuration
^^^^^^^^^^^^^

The configuration requires a `service account token <https://grafana.com/docs/grafana/latest/administration/service-accounts/>`_
from your Grafana instance.

.. code-block:: yaml

    holmes:
        toolsets:
            grafana/loki:
                enabled: true
                config:
                    api_key: <your grafana API key>
                    url: https://xxxxxxx.grafana.net # Your Grafana cloud account URL

You can optionally tweak the search terms used by the toolset. This is only needed if your Loki logs settings for pod,
namespace and node differ from the defaults listed below. To do so, add these search keys to the configuration:

.. code-block:: yaml

    holmes:
        toolsets:
            grafana/loki:
                enabled: true
                config:
                    api_key: <your grafana API key>
                    url: https://xxxxxxx.grafana.net # Your Grafana cloud account URL
                    pod_name_search_key: "pod"
                    namespace_search_key: "namespace"
                    node_name_search_key: "node"

.. include:: ./_toolset_configuration.inc.rst

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
Tempo to debug performance related issues.


Configuration
^^^^^^^^^^^^^

Tempo is configured the using the same Grafana settings as the Grafana Loki toolset. The configuration requires
a `service account token <https://grafana.com/docs/grafana/latest/administration/service-accounts/>`_ from
your Grafana instance.

.. code-block:: yaml

    holmes:
        toolsets:
            grafana/tempo:
                enabled: true
                config:
                    api_key: <your grafana API key>
                    url: https://xxxxxxx.grafana.net # Your Grafana cloud account URL

.. include:: ./_toolset_configuration.inc.rst

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
