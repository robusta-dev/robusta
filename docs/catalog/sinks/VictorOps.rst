VictorOps
##########

Robusta can send playbooks results to the VictorOps alerts API.

| To configure VictorOps, We need an VictorOps REST endpoint (url).
| Consult the VictorOps `REST endpoint integration guide <https://help.victorops.com/knowledge-base/rest-endpoint-integration-guide/#:~:text=In%20VictorOps%2C%20click%20on%20Integrations,preferred%20method%20to%20create%20incidents>`_.

Configuring the VictorOps sink
------------------------------------------------

.. admonition:: values.yaml

    .. code-block:: yaml

        sinks_config:
            - victorops_sink:
                name: main_victorops_sink
                url: <REST endpoint>
**Example Output:**

.. admonition:: Typically you'll send alerts from Robusta to VictorOps and not deployment changes. We're showing a non-typical example with deployment changes because it helps compare the format with other sinks.

    .. image:: /images/deployment-babysitter-victorops.png
      :width: 1000
      :align: center
