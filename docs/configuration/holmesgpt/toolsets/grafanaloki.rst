Loki (Grafana)
===============

By enabling this toolset, HolmesGPT will be able to query logs from `Loki <https://grafana.com/oss/loki/>`_
by proxying through a `Grafana <https://grafana.com/oss/grafana/>`_ instance.

After this toolset is enabled, you can ask Holmes questions like: *Look at my cluster with kubectl, pick an arbitrary node, then fetch logs from loki for that node. Summarize all problems you find.*

Prerequisites
^^^^^^^^^^^^^
A `Grafana service account token <https://grafana.com/docs/grafana/latest/administration/service-accounts/>`_
with the following permissions:

* Basic role -> Viewer
* Data sources -> Reader

Check out this `video <https://www.loom.com/share/f969ab3af509444693802254ab040791?sid=aa8b3c65-2696-4f69-ae47-bb96e8e03c47>`_ on creating a Grafana service account token.

Getting Grafana URL
-----------------------

You can find the Grafana URL required for Loki and Tempo in your Grafana cloud account settings. 

.. image:: /images/grafana-url-for-holmes.png
  :width: 600
  :align: center

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
                api_key: <your grafana service account token>
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
                api_key: <your grafana service account token>
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
              api_key: <your grafana service account token>
              url: <your grafana url> # e.g. https://acme-corp.grafana.net 
    
    You can optionally tweak the search terms used by the toolset. This is only needed if your Loki logs settings for pod,
    namespace and node differ from the defaults listed below. To do so, add these search keys to the configuration:

    .. code-block:: yaml

      toolsets:
        grafana/loki:
          enabled: true
          config:
              api_key: <your grafana service account token>
              url: <your grafana url> # e.g. https://acme-corp.grafana.net 
            pod_name_search_key: "pod"
            namespace_search_key: "namespace"
            node_name_search_key: "node"

    To test, run: 

    .. code-block:: yaml
      
        holmes ask "Which applications have an issue and check the logs on loki for the reasons"

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



