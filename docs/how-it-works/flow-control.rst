Playbook Execution
################################

An alert arrives in Robusta, something magical happens, and out comes a perfect Slack message with details why the alert fired.


.. image:: /images/prometheus-alert-without-robusta.png
    :width: 800px

You :ref:`already know <Automatically investigate a Prometheus alert>` that this magic is *configured* with a few lines of YAML like this:

.. code-block:: yaml

    - triggers:
      - on_prometheus_alert:
          alert_name: KubePodCrashLooping
      actions:
      - logs_enricher: {}

But what happens under the hood? How does Robusta process these triggers and actions?

What is a playbook?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Everything starts with playbooks. A playbook is some condition (a *trigger*) combined with instructions (an *action*)
defining what to do.

What are playbook triggers?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Playbooks are *event-driven*. They start running when triggered.

Each trigger fires at a distinct moment in time when something interesting happened in your cluster. Some triggers are:

* on_prometheus_alert
* on_deployment_update
* on_pod_crash_loop

Robusta is constantly listening to the cluster, evaluating it's triggers, and checking if it's time to run playbooks.

Playbooks can have more than one trigger, in which case *any* trigger is sufficient to start the playbook's execution.

What are playbook actions?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Actions do something. They respond to the trigger by collecting information, investigating, or even fixing the problem.

A single playbook can have multiple actions, in which case they'll be executed in order.

What happens if multiple triggers match an event?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
All relevant playbooks will run, in the order they were defined. For example:

.. code-block:: yaml

   - triggers:  # playbook A
     - on_deployment_create: {}
     actions:
     - my_first_action: {}
   - triggers:  # playbook B
     - on_deployment_create: {}
     actions:
     - my_second_action: {}

In the example above, ``playbook A`` will run before ``playbook B``

Stop Processing
^^^^^^^^^^^^^^^^^^
Any action can :ref:`stop the processing flow <stop_processing>` if needed. No further actions will run.

This is how actions like :ref:`node_restart_silencer <node_restart_silencer>` work.

Only actions that appear **after** the current action will be stopped. This means, for example, that silencers must appear before other playbooks.
