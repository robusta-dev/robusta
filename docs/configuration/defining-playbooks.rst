.. _defining-playbooks:

Custom Playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A playbook is an automation rule for detecting, investigating, or fixing problems in your cluster.

For an introduction on why playbooks are useful, see :ref:`How it Works <how-it-works-index>`.

This guide covers syntax for defining your own playbooks.

My first playbook
--------------------

Playbooks are defined using the ``customPlaybooks`` Helm value. To apply them, you edit your Helm values and perform an upgrade.

Lets define a playbook to notify about failed Liveness probes:

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

Every playbook has two sections: ``triggers`` and ``actions``. Triggers define *when* a playbook should be activated.
Actions define *what* a playbook should do.

How Triggers Work
----------------------
Triggers define when a playbook runs. View the full list of triggers in the Triggers Reference.

Triggers have parameters that restrict when they fire:

- triggers:
  - on_pod_crash_loop:
      restart_reason: "CrashLoopBackOff"
      name_prefix: fluentbit
      namespace_prefix: kube-system

Most Kubernetes-related triggers support at least ``name`` and ``namespace``.

How Actions Work
----------------------
Actions define what to do. For a list of all actions, see here.

How Notifications Work
------------------------

Playbook actions can generate notifications, automatically fix issues, or both.

Creating a New Notification
*****************************

To create a custom notification use the ``create_finding`` action. In Robusta, notifications are called *findings*:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_job_failure:
          namespace_prefix: robusta
      actions:
      - create_finding:
          title: "Job $name on namespace $namespace failed"
          aggregation_key: "Job Failure"

TODO: show screenshot.

Adding Details to Notifications
********************************
You can add details to notifications by running appropriate actions. All the actions that you run should match the
type of trigger. For example, the trigger ``on_job_failure`` supports actions like ``job_events_enricher``, which runs
``kubectl get events`` applies a filter, and attaching all events related to the Job that triggered this playbook.

TODO: show screenshot.


The order of actions within a specific playbook is important. Some actions create notifications and others merely attach
data to an existing notification. If actions that attach data run before actions that create the notification, a default
notification will be created for the first action and a separate notification message will be created for the second action.

TODO: show screenshot.

Some actions both create a notification and attach data to it. For example, the ``report_crash_loop`` action generates a
notification about a crashing pod and also attaches logs:

TODO: show screenshot

Multiple Playbook Instances
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

If the triggers in multiple playbooks match the same incoming event, all relevant playbooks will run.
See :ref:`Flow Control` to understand the order they run in.

Global Configuration for Playbook Parameters
--------------------------------------------------

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


Robusta is a rules engine, as described in :ref:`How it Works <how-it-works-index>` and :ref:`What are Playbooks <What are Playbooks?>`. These rules are called playbooks.
