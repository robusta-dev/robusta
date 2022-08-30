Defining playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Playbooks are defined using the ``customPlaybooks`` Helm value.

Every playbooks has three parts: triggers, actions, and sinks. See the :ref:`Automation Basics` tutorial for
a walkthrough.

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_deployment_update:
      actions:
      - resource_babysitter:
          fields_to_monitor: ["status.conditions"]
      sinks:
      - "main_slack_sink"

Configuring triggers
----------------------
Triggers define when a playbook runs:

.. code-block:: yaml
    :emphasize-lines: 3-4

    customPlaybooks:
      - triggers:
          - on_deployment_update:
              name_prefix: MyApp
        actions:
          - resource_babysitter:
              fields_to_monitor: ["status.conditions"]
        sinks:
          - "main_slack_sink"

.. note::

    In the yaml, ``triggers`` is an array, but currently it must contain exactly one entry.

Most triggers support extra filters like ``name_prefix`` which further restricts the trigger.

If multiple triggers match, multiple playbooks will run according to the rules in :ref:`Flow Control`

Multiple playbook instances
-----------------------------------

You can enable a playbook multiple times with different configurations:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_deployment_update:
          name_prefix: MyApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_api_key: grafana_key_goes_here
          grafana_dashboard_uid: id_for_dashboard1
          grafana_url: http://grafana.namespace.svc
      sinks:
      - "main_slack_sink"

    - triggers:
      - on_deployment_update:
          name_prefix: OtherApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_api_key: grafana_key_goes_here
          grafana_dashboard_uid: id_for_dashboard2
          grafana_url: http://grafana.namespace.svc
      sinks:
      - "main_slack_sink"

