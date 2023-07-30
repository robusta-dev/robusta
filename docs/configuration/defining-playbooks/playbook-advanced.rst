.. _playbooks-201:

Advanced Playbook Techniques
################################

This guide assumes you already know :ref:`playbook basics <Playbook Basics>` and how to :ref:`create notifications <Creating Notifications>`. It explains
implementation details and common techniques.

Using Filters to Restrict Triggers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many triggers have parameters that restrict when they fire:

.. code-block::

    - triggers:
      - on_pod_crash_loop:
          restart_reason: "CrashLoopBackOff"
          name_prefix: fluentbit
          namespace_prefix: kube-system

Most Kubernetes-related triggers support at least ``name`` and ``namespace``. Refer to :ref:`Triggers Reference` for
details.

Running Multiple Playbooks on the Same Event
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If multiple triggers match an incoming event, all relevant playbooks execute in the order they were defined. For example:

.. code-block:: yaml

   # first playbook
   - triggers:
     - on_deployment_create: {}
     actions:
     - my_first_action: {}

   # second playbook
   - triggers:
     - on_deployment_create: {}
     actions:
     - my_second_action: {}

In the example above, ``my_first_action`` runs before ``my_second_action``.

Multiple Playbook Instances
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Likewise, you can enable identical playbooks multiple times with different parameters:

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

If the triggers in multiple playbooks match the same incoming event, all relevant playbooks will run.

Global Configuration for Playbook Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the previous example, ``grafana_api_key`` and ``grafana_url`` were defined multiple times with the same value.

To avoid repeating yourself, you can define parameters globally for all playbooks. These parameters will be applied to
any action or trigger which expects a parameter with the same name.

.. code-block:: yaml

   globalConfig:
     cluster_name: "my-staging-cluster"
     grafana_api_key: "grafana_key_goes_here"
     grafana_url: http://grafana.namespace.svc

    customPlaybooks:
    - triggers:
      - on_deployment_update:
          name_prefix: MyApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_dashboard_uid: id_for_dashboard1
      sinks:
      - "main_slack_sink"

    - triggers:
      - on_deployment_update:
          name_prefix: OtherApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_dashboard_uid: id_for_dashboard2
      sinks:
      - "main_slack_sink"

Stopping Playbook Execution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An action can :ref:`stop the processing flow <stop_processing>` if needed, preventing subsequent actions from being run.

This is useful for *silencing* actions like :ref:`node_restart_silencer <node_restart_silencer>`. These actions
need to stop alerts from being propogated to other playbooks.

Only actions following the current action will be stopped. Therefore, silencers must be defined before other playbooks.
