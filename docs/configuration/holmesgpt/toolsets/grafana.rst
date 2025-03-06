Grafana
=======

.. _toolset_grafana_loki:

Loki
----

By enabling this toolset, HolmesGPT will fetch node and pods logs from `Loki <https://grafana.com/oss/loki/>`_
by proxying through a `Grafana <https://grafana.com/oss/grafana/>`_ instance.

You **should** enable this toolset to replace the default :ref:`kubernetes/logs <toolset_kubernetes_logs>`
toolset if all your kubernetes/pod logs are consolidated inside Loki. It will make it easier for HolmesGPT
to fetch incident logs, including the ability to precisely consult past logs.

Configuration
^^^^^^^^^^^^^

The configuration requires a `service account token <https://grafana.com/docs/grafana/latest/administration/service-accounts/>`_
from Grafana.

.. code-block:: yaml

    holmes:
        toolsets:
            grafana/loki:
                enabled: true
                config:
                    api_key: <your grafana API key>
                    url: https://grafana-url
                    grafana_datasource_uid: <the UID of the loki data source in Grafana>
                    labels:
                        pod: "pod"
                        namespace: "namespace"

            kubernetes/logs:
                enabled: false # Disable HolmesGPT's default logging mechanism

.. include:: ./_toolset_configuration.inc.rst

You can tweak the labels used by the toolset to identify kubernetes resources. This is only needed if your
Loki logs settings for ``pod``, and ``namespace`` differ from the defaults in the example above.

Use the following commands to list Loki's labels and determine which ones to use:

.. code-block:: bash

    # Make Loki accessible locally
    kubectl port-forward svc/loki 3100:3100

    # List all labels. You may have to add the -H 'X-Scope-OrgID:<org id>' option with a valid org id
    curl http://localhost:3100/loki/api/v1/labels


If Loki is your primary datasource for logs, it is **advised** to disable the default HolmesGPT logging
tool by disabling the ``kubernetes/logs`` toolset. Without this. HolmesGPT may still use kubectl to
fetch logs instead of Loki.

.. code-block:: yaml

    holmes:
        toolsets:
            kubernetes/logs:
                enabled: false

**Obtaining the datasource UID**

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
        "name": "Loki-kubernetes",
        "type": "loki",
        "typeName": "Loki",
        "typeLogoUrl": "/public/app/plugins/datasource/loki/img/loki_icon.svg",
        "access": "proxy",
        "url": "http://loki.loki:3100",
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
    # In this case, there is a single Loki datasources which UID
    # is "klja8hsa-8a9c-4b35-1230-7baab22b02ee"

Capabilities
^^^^^^^^^^^^

.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - fetch_loki_logs_for_resource
     - Fetches the Loki logs for a given kubernetes resource
   * - fetch_loki_logs
     - Fetches Loki logs from any query


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
                    grafana_datasource_uid: <the UID of the tempo data source in Grafana>

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
