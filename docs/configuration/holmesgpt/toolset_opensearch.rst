Opensearch
====

Provide cluster metadata information like health, shards, settings.

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
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
                            header1: foo
                          use_ssl: bool = True
                          ssl_assert_hostname: bool = False
                          verify_certs: bool = False
                          ssl_show_warn: bool = False
                          http_auth:
                            username: str
                            password: str


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
