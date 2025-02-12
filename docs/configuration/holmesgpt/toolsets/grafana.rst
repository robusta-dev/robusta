Grafana
=======

Loki
----

By enabling this toolset, HolmesGPT will be able to consult logs from `Loki <https://grafana.com/oss/loki/>`_
by proxying through a `Grafana <https://grafana.com/oss/grafana/>`_ instance.

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
                    url: https://grafana-url
                    pod_name_search_key: "pod"
                    namespace_search_key: "namespace"
                    node_name_search_key: "node"


.. details:: Tweaking search terms

    You can optionally tweak the search terms used by the toolset. This is only needed if your Loki logs
    settings for pod, namespace and node differ from the above defaults.

    To do so, set any of the following configuration setting as it is described above:

    * ``pod_name_search_key``: Loki search key for pods
    * ``namespace_search_key``: Loki search key for namespaces
    * ``node_name_search_key``: Loki search key for nodes

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
                    url: https://grafana-url

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
