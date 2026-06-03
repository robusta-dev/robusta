DataDog
##########

.. admonition:: This page documents a legacy sink in Robusta classic
   :class: warning

   You probably want `HolmesGPT <https://holmesgpt.dev/>`_ instead.

   Sinks statically forward every notification to a fixed destination. Modern Robusta instead investigates and routes alerts **agentically**, using :ref:`triggered workflows <defining-playbooks>` together with `MCP servers <https://holmesgpt.dev/data-sources/remote-mcp-servers/?tab=robusta-helm-chart>`_, so the LLM makes intelligent triage decisions about each alert instead of blindly forwarding everything.


Robusta can report issues and events in your cluster to the Datadog events API.

Example Output:

    .. image:: /images/deployment-babysitter-datadog.png
        :width: 1000
        :align: center

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
