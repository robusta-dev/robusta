.. _toolset_grafana_loki:

Loki (Grafana)
===============

By enabling this toolset, HolmesGPT will fetch node and pods logs from `Loki <https://grafana.com/oss/loki/>`_
by proxying through a `Grafana <https://grafana.com/oss/grafana/>`_ instance.

You **should** enable this toolset to replace the default :ref:`kubernetes/logs <toolset_kubernetes_logs>`
toolset if all your kubernetes/pod logs are consolidated inside Loki. It will make it easier for HolmesGPT
to fetch incident logs, including the ability to precisely consult past logs.


.. include:: ./_toolsets_that_provide_logging.inc.rst

Prerequisites
^^^^^^^^^^^^^

A `Grafana service account token <https://grafana.com/docs/grafana/latest/administration/service-accounts/>`_
with the following permissions:

* Basic role -> Viewer
* Data sources -> Reader

Check out this `video <https://www.loom.com/share/f969ab3af509444693802254ab040791?sid=aa8b3c65-2696-4f69-ae47-bb96e8e03c47>`_ on creating a Grafana service account token.

Getting Grafana URL
-----------------------

You can find the Grafana URL required for Loki in your Grafana cloud account settings.

.. image:: /images/grafana-url-for-holmes.png
  :width: 600
  :align: center


Obtaining the datasource UID
-----------------------------------

You may have multiple Loki data sources setup in Grafana. HolmesGPT uses a single Loki datasource to
fetch the logs and it needs to know the UID of this datasource.

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
    # In this case, there is a single Loki datasourceUID
    # with UID "klja8hsa-8a9c-4b35-1230-7baab22b02ee"


Configuration
^^^^^^^^^^^^^


.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chat

    .. code-block:: yaml

      holmes:
        toolsets:
          grafana/loki:
            enabled: true
            config:
              api_key: <your grafana API key>
              url: https://xxxxxxx.grafana.net # Your Grafana cloud account URL
              grafana_datasource_uid: <the UID of the loki data source in Grafana>
              labels:
                pod: "pod"
                namespace: "namespace"

          kubernetes/logs:
            enabled: false # Disable HolmesGPT's default logging mechanism


    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    Add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

      toolsets:
        grafana/loki:
          enabled: true
          config:
            api_key: <your grafana API key>
            url: https://xxxxxxx.grafana.net # Your Grafana cloud account URL
            grafana_datasource_uid: <the UID of the loki data source in Grafana>
            labels:
                pod: "pod"
                namespace: "namespace"

        kubernetes/logs:
          enabled: false # Disable HolmesGPT's default logging mechanism


**Search labels**

You can tweak the labels used by the toolset to identify kubernetes resources. This is only needed if your
Loki logs settings for ``pod``, and ``namespace`` differ from the defaults in the example above.

Use the following commands to list Loki's labels and determine which ones to use:

.. code-block:: bash

    # Make Loki accessible locally
    kubectl port-forward svc/loki 3100:3100

    # List all labels. You may have to add the -H 'X-Scope-OrgID:<org id>' option with a valid org id
    curl http://localhost:3100/loki/api/v1/labels


**Disabling the default toolset**

If Loki is your primary datasource for logs, it is **advised** to disable the default HolmesGPT logging
tool by disabling the ``kubernetes/logs`` toolset. Without this. HolmesGPT may still use kubectl to
fetch logs instead of Loki.

.. code-block:: yaml

    holmes:
        toolsets:
            kubernetes/logs:
                enabled: false


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
