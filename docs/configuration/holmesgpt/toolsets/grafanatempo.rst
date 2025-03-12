
Tempo (Grafana)
================

By enabling this toolset, HolmesGPT will be able to fetch trace information from Grafana
Tempo to debug performance related issues, like high latency in your application.

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
              api_key: <your grafana service account token>
              url: <your grafana url> # e.g. https://acme-corp.grafana.net 

    To test, run: 

    .. code-block:: yaml
      
        holmes ask "The payments DB is very slow, check tempo for any trace data"

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

