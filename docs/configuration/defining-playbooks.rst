Custom playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:ref:`Robusta is a rules engine <What is Robusta>`. These rules are called playbooks.

Every playbook has two main parts:

* :ref:`Triggering conditions <Defining Triggers>` (*when* should this playbook run)
* :ref:`Actions to perform <Defining Actions>` (*what* should this playbook do)

To define playbooks, you use the ``customPlaybooks`` Helm value. For example:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_kubernetes_warning_event_create:
            include: ["Liveness"]   # fires on failed Liveness probes
      actions:
        - customise_finding:
            severity: HIGH
            title: "Failed liveness probe: $name"
        - event_resource_events: {}

👆 Here, the generating trigger is a Kubernetes event. There are many triggers available, including Prometheus alerts, crashing pods, and OOMKills.

Defining Triggers
----------------------
Triggers define when a playbook runs. For a list of all triggers, see here.

Most triggers support filters that further restrict when the trigger fires. For example:

``name_prefix`` which further restricts the trigger.

If multiple triggers match, multiple playbooks will run according to the rules in :ref:`Flow Control`

Defining Actions
----------------------
Actions define what to do. For a list of all actions, see here.

Most triggers support filters that further restrict when the trigger fires. For example:

``name_prefix`` which further restricts the trigger.

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

