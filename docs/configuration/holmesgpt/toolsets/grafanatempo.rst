
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

You can find the Grafana URL required for Tempo in your Grafana cloud account settings.

.. image:: /images/grafana-url-for-holmes.png
  :width: 600
  :align: center


Obtaining the datasource UID
-----------------------

You may have multiple Tempo data sources setup in Grafana. HolmesGPT uses a single Tempo datasource to
fetch the traces and it needs to know the UID of this datasource.

A simple way to get the datasource UID is to access the Grafana API by running the following request:

.. code-block:: bash

    # port forward if you are using Robusta's grafana from your kubernetes cluster
    kubectl port-forward svc/robusta-grafana 3000:80

    # List the loki data sources
    curl -s -u <username>:<password> http://localhost:3000/api/datasources | jq '.[] | select(.type == "loki")'
    {
        "id": 2,
        "uid": "klja8hsa-8a9c-4b35-1230-7baab22b02ee",
        "orgId": 1,
        "name": "Tempo-kubernetes",
        "type": "tempo",
        "typeName": "Tempo",
        "typeLogoUrl": "/public/app/plugins/datasource/tempo/img/tempo_icon.svg",
        "access": "proxy",
        "url": "http://tempo.tempo:3100",
        "user": "",
        "database": "",
        "basicAuth": false,
        "isDefault": false,
        "jsonData": {
            "httpHeaderName1": "admin",
            "httpHeaderName2": "X-Scope-OrgID",
            "tlsSkipVerify": true
        },
        "readOnly": false
    }
    # In this case, there is a single Tempo datasourceUID
    # with UID "klja8hsa-8a9c-4b35-1230-7baab22b02ee"


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
              grafana_datasource_uid: <the UID of the tempo data source in Grafana>

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
              grafana_datasource_uid: <the UID of the tempo data source in Grafana>

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
