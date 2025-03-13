Kafka
=====

By enabling this toolset, HolmesGPT will be able to fetch metadata from Kafka. This provides Holmes
the ability to introspect into Kafka by listing consumers and topics or finding lagging consumer groups.

This toolset uses the AdminClient of the
`confluent-kafka python library <https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#pythonclient-adminclient>`_.
Kafka's `Java API <https://docs.confluent.io/platform/current/installation/configuration/admin-configs.html>`_
is also a good source of documentation.

Configuration
-------------

.. code-block:: yaml

    holmes:
        toolsets:
            kafka/admin:
                enabled: true
                config:
                    kafka_clusters:
                        - name: aks-prod-kafka
                          kafka_broker: kafka-1.aks-prod-kafka-brokers.kafka.svc:9095
                          kafka_username: kafka-plaintext-user
                          kafka_password: ******
                          kafka_sasl_mechanism: SCRAM-SHA-512
                          kafka_security_protocol: SASL_PLAINTEXT
                        - name: gke-stg-kafka
                          kafka_broker: gke-kafka.gke-stg-kafka-brokers.kafka.svc:9095
                          kafka_username: kafka-plaintext-user
                          kafka_password: ****
                          kafka_sasl_mechanism: SCRAM-SHA-512
                          kafka_security_protocol: SASL_PLAINTEXT

Below is a description of the configuration field for each cluster:

.. list-table::
  :header-rows: 1
  :widths: 20 80

  * - Config key
    - Description
  * - name
    - Give a meaningful name to your cluster. Holmes will use it to decide what cluster to look into. Names must be unique across all clusters.
  * - kafka_broker
    - List of host/port pairs to use for establishing the initial connection to the Kafka cluster. Comma separated values.
  * - kafka_client_id
    - An id string to pass to the server when making requests. The purpose of this is to be able to track the source of requests beyond just ip/port by allowing a logical application name to be included in server-side request logging.
  * - kafka_security_protocol
    - Protocol used to communicate with brokers. Valid values are: PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL
  * - kafka_sasl_mechanism
    - SASL mechanism used for client connections. This may be any mechanism for which a security provider is available. GSSAPI is the default mechanism.
  * - kafka_username
    - Sets the SASL credentials used for this client. This key sets the username.
  * - kafka_password
    - Sets the SASL credentials used for this client. This key sets the password.

.. include:: ./_toolset_configuration.inc.rst

Capabilities
------------
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - list_kafka_clusters
     - Lists all configured Kafka clusters
   * - list_kafka_consumers
     - Lists all Kafka consumer groups in the cluster
   * - describe_consumer_group
     - Describes a specific Kafka consumer group
   * - list_topics
     - Lists all Kafka topics in the cluster
   * - describe_topic
     - Describes details of a specific Kafka topic
   * - find_consumer_groups_by_topic
     - Finds all consumer groups consuming from a specific topic
