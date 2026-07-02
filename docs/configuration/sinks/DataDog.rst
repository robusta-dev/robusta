DataDog
##########

.. admonition:: This page documents a legacy sink in Robusta classic
   :class: warning

   For new setups, we recommend `HolmesGPT <https://holmesgpt.dev/>`_ instead.

   HolmesGPT triages your alerts instead of just forwarding them. Sinks are deterministic: they send every notification, unchanged, to a fixed destination, leaving you to read and prioritize each one yourself.

   HolmesGPT instead uses AI to investigate each alert, surface the likely root cause, and escalate only what needs attention — so you get fewer, more actionable notifications. Set this up with `Alerts Triage <https://platform.robusta.dev/holmes/alerts-triage>`_ for alerts, or :ref:`Triggered Workflows <defining-playbooks>` for custom events.


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
