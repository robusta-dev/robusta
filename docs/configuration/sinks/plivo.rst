Plivo
#################

.. admonition:: This page documents a legacy sink in Robusta classic
   :class: warning

   For new setups, we recommend `HolmesGPT <https://holmesgpt.dev/>`_ instead.

   HolmesGPT triages your alerts instead of just forwarding them. Sinks are deterministic: they send every notification, unchanged, to a fixed destination, leaving you to read and prioritize each one yourself.

   HolmesGPT instead uses AI to investigate each alert, surface the likely root cause, and escalate only what needs attention — so you get fewer, more actionable notifications. Set this up with `Alerts Triage <https://platform.robusta.dev/holmes/alerts-triage>`_ for alerts, or :ref:`Triggered Workflows <defining-playbooks>` for custom events.


Robusta can send SMS notifications about issues and events in your Kubernetes cluster to a phone number using Plivo.

Getting your Auth ID and Auth Token
------------------------------------------------
Log in to the Plivo console at `cx.plivo.com <https://cx.plivo.com/?utm_source=github&utm_medium=oss&utm_campaign=robusta>`_. Your Auth ID and Auth Token are shown on the dashboard.

Getting a sender number
------------------------------------------------
You need an SMS enabled Plivo phone number to send from. Buy or view your numbers in the Plivo console under Phone Numbers.

Configuring the Plivo sink
------------------------------------------------
Now we're ready to configure the Plivo sink.

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - plivo_sink:
            name: plivo_sink
            auth_id: <YOUR_PLIVO_AUTH_ID>
            auth_token: <YOUR_PLIVO_AUTH_TOKEN>
            from_number: <YOUR_PLIVO_NUMBER> # E.164 format, e.g. +14155551234
            to_number: <DESTINATION_NUMBER> # E.164 format; for several recipients join them with '<'

.. note::

    Numbers use E.164 format. To send to more than one recipient, join the numbers with ``<`` (for example ``+14155551234<+14155555678``).

Save the file and run

.. code-block:: bash
   :name: cb-add-plivo-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

You should now get playbook results as SMS messages from Plivo.
