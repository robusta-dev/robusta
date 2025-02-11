Opensearch
====

By enabling this toolset, HolmesGPT will be able to access cluster metadata information
like health, shards, and settings. This allows HolmesGPT to better troubleshoot problems
with one or more opensearch clusters.

Configuration
-------------

.. code-block:: yaml

    holmes:
        toolsets:
            opensearch:
                enabled: true
                config:
                    opensearch_clusters:
                        - hosts:
                            - host1.com
                            - host2.com
                          headers:
                            header1: "value1"
                          use_ssl: <boolean>
                          ssl_assert_hostname: <boolean>
                          verify_certs: <boolean>
                          ssl_show_warn: <boolean>
                          http_auth:
                            username: <basic auth username>
                            password: <basic auth password>

.. include:: ./_toolset_configuration.inc.rst

Capabilities
------------
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - opensearch_list_shards
     - List the shards within an opensearch cluster
   * - opensearch_get_cluster_settings
     - Retrieve the cluster's settings
   * - opensearch_get_cluster_health
     - Retrieve the cluster's health
