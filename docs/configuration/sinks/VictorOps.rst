VictorOps
##########

Robusta can report issues and events in your Kubernetes cluster to the VictorOps alerts API.

| To configure VictorOps, a VictorOps REST endpoint (url) is needed.
| Consult the VictorOps `REST endpoint integration guide <https://help.victorops.com/knowledge-base/rest-endpoint-integration-guide/#:~:text=In%20VictorOps%2C%20click%20on%20Integrations,preferred%20method%20to%20create%20incidents>`_.

Configuring the VictorOps sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
            - victorops_sink:
                name: main_victorops_sink
                url: <REST endpoint> # e.g. https://alert.victorops.com/integrations/generic/20131114/alert/4a6a87eb-fca9-4117-931a-c842277ea90a/$routing_key

Save the file and run

.. code-block:: bash
   :name: cb-add-victorops-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

.. note::

   To secure your REST endpoint URL using Kubernetes Secrets, see :ref:`Managing Secrets`.

**Example Output:**

.. admonition:: Typically you'll send alerts from Robusta to VictorOps and not deployment changes. We're showing a non-typical example with deployment changes because it helps compare the format with other sinks.

    .. image:: /images/deployment-babysitter-victorops.png
      :width: 1000
      :align: center
