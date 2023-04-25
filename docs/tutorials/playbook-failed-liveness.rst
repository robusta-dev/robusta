Track Failed Liveness Probes
##############################

Lets track failed Liveness Probes and notify the user. Notifications will be sent to all configured :ref:`Sinks <Sinks Reference>`
like Slack, MSTeams, or DataDog. It is also possible to :ref:`route notifications to specific sinks<Routing Alerts to Specific Sinks>`.

Defining a Playbook
-----------------------------------------------------

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_kubernetes_warning_event_create:
            include: ["Liveness"]   # fires on failed Liveness probes
      actions:
        - create_finding:
            severity: HIGH
            title: "Failed liveness probe: $name"
        - event_resource_events: {}

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Testing Your Playbook
------------------------------------------

TODO: add demo to kubernetes-demos repo and reference it here
Show screenshot of result

How it Works
-------------

TODO

.. TODO: improve based on comments at https://github.com/robusta-dev/robusta/issues/799#event-8873234835