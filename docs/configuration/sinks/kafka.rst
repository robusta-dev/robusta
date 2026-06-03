Kafka
#########

.. admonition:: This page documents a legacy sink in Robusta classic
   :class: warning

   You probably want `HolmesGPT <https://holmesgpt.dev/>`_ instead.

   Sinks statically forward every notification to a fixed destination. Modern Robusta instead investigates and routes alerts **agentically**, using :ref:`triggered workflows <defining-playbooks>` together with `MCP servers <https://holmesgpt.dev/data-sources/remote-mcp-servers/?tab=robusta-helm-chart>`_, so the LLM makes intelligent triage decisions about each alert instead of blindly forwarding everything.


Robusta can report issues and events in your Kubernetes cluster to a Kafka topic.

Configuring the Kafka sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - kafka_sink:
            name: kafka_sink
            kafka_url: "localhost:9092"
            topic: "robusta-playbooks"

.. admonition:: Add this to your generated_values.yaml if configuring with authentication

   `additional auth options <https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html#kafkaproducer>`_

   .. code-block:: yaml

        sinksConfig:
        - kafka_sink:
            name: kafka_sink
            kafka_url: "localhost:9096"
            topic: "robusta-playbooks"
            auth:
                sasl_mechanism: SCRAM-SHA-512
                security_protocol: SASL_SSL
                sasl_plain_username: robusta
                sasl_plain_password: password

Save the file and run

.. code-block:: bash
   :name: cb-add-kafka-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml


**Example Output:**

    .. image:: /images/deployment-babysitter-kafka.png
      :width: 400
      :align: center
