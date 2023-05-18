Kafka
#########

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

Save the file and run

.. code-block:: bash
   :name: cb-add-kafka-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml


**Example Output:**

    .. image:: /images/deployment-babysitter-kafka.png
      :width: 400
      :align: center
