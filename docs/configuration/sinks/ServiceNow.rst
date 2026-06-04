ServiceNow
#################

.. admonition:: This page documents a legacy sink in Robusta classic
   :class: warning

   For new setups, we recommend `HolmesGPT <https://holmesgpt.dev/>`_ instead.

   HolmesGPT triages your alerts instead of just forwarding them. Sinks are deterministic: they send every notification, unchanged, to a fixed destination, leaving you to read and prioritize each one yourself.

   HolmesGPT instead uses AI to investigate each alert, surface the likely root cause, and escalate only what needs attention — so you get fewer, more actionable notifications. Set this up with `Alerts Triage <https://platform.robusta.dev/holmes/alerts-triage>`_ for alerts, or :ref:`Triggered Workflows <defining-playbooks>` for custom events.


Robusta can report issues and events in your Kubernetes cluster by creating
issues in ServiceNow.

.. image:: /images/servicenow_image.png
  :width: 600
  :align: center

Configuring the ServiceNow Sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - service_now_sink:
            name: robusta_integration
            instance: serviceNow_id
            username: admin
            password: SecurePassword@123
            caller_id: robusta_bot

* ``instance``: Your ServiceNow instance identifier.
* ``caller_id`` (optional): Used to specify a user for the "Caller" field in ServiceNow incidents. If not set, this field defaults to "(empty)". It's advisable to create a dedicated user, like "robusta_bot", to easily track incidents from Robusta.


Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.
