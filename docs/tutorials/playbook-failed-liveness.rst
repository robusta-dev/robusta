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
            aggregation_key: "Failed Liveness Probe"
            severity: HIGH
            title: "Failed liveness probe: $name"
        - event_resource_events: {}

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Testing Your Playbook
------------------------------------------

Apply the following command the create a failing liveness probe.

.. code-block:: yaml

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/liveness_probe_fail/failing_liveness_probe.yaml


.. details:: Output

    .. image:: /images/failedlivenessprobe.png
        :alt: Failed liveness probe notification on Slack
        :align: center

How it Works
-------------


TODO

.. TODO: improve based on comments at https://github.com/robusta-dev/robusta/issues/799#event-8873234835
