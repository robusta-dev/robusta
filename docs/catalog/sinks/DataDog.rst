DataDog 
##########

Robusta can send playbooks results to the Datadog events API.

To configure datadog sink, we need a DataDog API key. The API key can be retrieved from your DataDog Account. 

Configuring the Datadog sink
------------------------------------------------

.. admonition:: values.yaml

    .. code-block:: yaml

        sinks_config:
        - datadog_sink:
            name: datadog_sink
            api_key: "datadog api key"


**Example Output:**

    .. image:: /images/deployment-babysitter-datadog.png
      :width: 1000
      :align: center
 