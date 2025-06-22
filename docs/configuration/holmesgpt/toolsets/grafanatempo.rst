
Tempo
=====

By enabling this toolset, HolmesGPT will be able to fetch trace information from Grafana
Tempo to debug performance related issues, like high latency in your application.

Proxying through Grafana
^^^^^^^^^^^^^^^^^^^^^^^^

This is the recommended approach because we intend to add more capabilities to the toolset that are only available with Grafana.

Prerequisites
-------------

A `Grafana service account token <https://grafana.com/docs/grafana/latest/administration/service-accounts/>`_
with the following permissions:

* Basic role -> Viewer
* Data sources -> Reader

Check out this `video <https://www.loom.com/share/f969ab3af509444693802254ab040791?sid=aa8b3c65-2696-4f69-ae47-bb96e8e03c47>`_ on creating a Grafana service account token.

**Getting Grafana URL**

You can find the Grafana URL required for Tempo in your Grafana cloud account settings.

.. image:: /images/grafana-url-for-holmes.png
  :width: 600
  :align: center

**Obtaining the datasource UID**

You may have multiple Tempo data sources setup in Grafana. HolmesGPT uses a single Tempo datasource to
fetch the traces and it needs to know the UID of this datasource.

A simple way to get the datasource UID is to access the Grafana API by running the following request:

.. code-block:: bash

    # port forward if you are using Robusta's grafana from your kubernetes cluster
    kubectl port-forward svc/robusta-grafana 3000:80
    # List the Tempo data sources
    curl -s -u <username>:<password> http://localhost:3000/api/datasources | jq '.[] | select(.type == "tempo")'
    {
        "id": 3,
        "uid": "klja8hsa-8a9c-4b35-1230-7baab22b02ee",
        "orgId": 1,
        "name": "Tempo",
        "type": "tempo",
        "typeName": "Tempo",
        "typeLogoUrl": "/public/app/plugins/datasource/tempo/img/tempo_icon.svg",
        "access": "proxy",
        "url": "http://tempo-query-frontend.tempo:3100",
        "user": "",
        "database": "",
        "basicAuth": false,
        "isDefault": false,
        "jsonData": {
            "tlsSkipVerify": true
        },
        "readOnly": false
    }
    # In this case, there is a single Tempo datasourceUID
    # with UID "klja8hsa-8a9c-4b35-1230-7baab22b02ee"

Configuration (grafana proxy)
-----------------------------

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    .. code-block:: yaml

      holmes:
        toolsets:
          grafana/tempo:
            enabled: true
            config:
              api_key: <your grafana API key>
              url: <your grafana url> # e.g. https://acme-corp.grafana.net
              grafana_datasource_uid: <the UID of the tempo data source in Grafana>
              labels:
                pod: "k8s.pod.name"
                namespace: "k8s.namespace.name"
                deployment: "k8s.deployment.name"
                node: "k8s.node.name"
                service: "service.name"

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

Direct connection
^^^^^^^^^^^^^^^^^

The toolset can directly connect to a Tempo instance without proxying through a Grafana instance.
This is done by not setting the ``grafana_datasource_uid`` field. Not setting this field makes HolmesGPT
assume that it is directly connecting to Tempo.

Configuration (direct connection)
---------------------------------

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    .. code-block:: yaml

      holmes:
        toolsets:
          grafana/tempo:
            enabled: true
            config:
              url: http://tempo.monitoring
              headers:
                X-Scope-OrgID: "<tenant id>" # Set the X-Scope-OrgID if tempo multitenancy is enabled


    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    Add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

      toolsets:
        grafana/tempo:
          enabled: true
          config:
            url: http://tempo.monitoring
            headers:
              X-Scope-OrgID: "<tenant id>" # Set the X-Scope-OrgID if tempo multitenancy is enabled


Advanced configuration
^^^^^^^^^^^^^^^^^^^^^^

**Search labels**

You can tweak the labels used by the toolset to identify kubernetes resources. This is only needed if the trace
labels differ from the defaults in the example above.


.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    .. code-block:: yaml

      holmes:
        toolsets:
          grafana/tempo:
            enabled: true
            config:
              url: ...
              labels:
                pod: "k8s.pod.name"
                namespace: "k8s.namespace.name"
                deployment: "k8s.deployment.name"
                node: "k8s.node.name"
                service: "service.name"

    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    Add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

      toolsets:
        grafana/tempo:
          enabled: true
          config:
            url: ...
            labels:
              pod: "k8s.pod.name"
              namespace: "k8s.namespace.name"
              deployment: "k8s.deployment.name"
              node: "k8s.node.name"
              service: "service.name"

Capabilities
^^^^^^^^^^^^
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - fetch_tempo_tags
     - List the tags available in Tempo
   * - fetch_tempo_traces
     - Lists Tempo traces. At least one of `service_name`, `pod_name` or `deployment_name` argument is required.
   * - fetch_tempo_trace_by_id
     - Retrieves detailed information about a Tempo trace using its trace ID. Use this to investigate a trace.
