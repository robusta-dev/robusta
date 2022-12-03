DataDog 
##########

Robusta can send playbooks results to the Datadog events API.

To configure datadog sink, we need a DataDog API key. The API key can be retrieved from your DataDog Account. 

Configuring the Datadog sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - datadog_sink:
            name: datadog_sink
            api_key: "datadog api key"

Save the file and run

.. code-block:: bash
   :name: cb-add-discord-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml


**Example Output:**

    .. image:: /images/deployment-babysitter-datadog.png
      :width: 1000
      :align: center
