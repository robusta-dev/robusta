Kafka 
######### 

Robusta can send playbook result to a Kafka topic.

Configuring the Kafka sink
------------------------------------------------

.. admonition:: values.yaml

    .. code-block:: yaml

        sinks_config:
        - kafka_sink:
            name: kafka_sink
            kafka_url: "localhost:9092"
            topic: "robusta-playbooks"
            default: false


**kafka:**

    .. image:: /images/deployment-babysitter-kafka.png
      :width: 400
      :align: center
