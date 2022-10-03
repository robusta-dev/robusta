Opsgenie
##########

Robusta can send playbooks results to the OpsGenie alerts API.

To configure OpsGenie, We need an OpsGenie API key. It can be configured using the OpsGenie team integration.

Configuring the OpsGenie sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinks_config:
        - opsgenie_sink:
            name: ops_genie_sink
            api_key: OpsGenie integration API key  # configured from OpsGenie team integration
            teams:
            - "noc"
            - "sre"
            tags:
            - "prod a"
            
Save the file and run

.. code-block:: bash
   :name: cb-add-opsgenie-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

**Example Output:**

.. admonition:: Typically you'll send alerts from Robusta to OpsGenie and not deployment changes. We're showing a non-typical example with deployment changes because it helps compare the format with other sinks.

    .. image:: /images/deployment-babysitter-opsgenie.png
      :width: 1000
      :align: center
