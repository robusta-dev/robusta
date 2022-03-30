Flow Control
################################

The :ref:`Configuration Guide` covers basic playbook definition.
This page explains how playbooks interact with one another.

Basics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Every Robusta playbook has a list of :ref:`Triggers` and a list of :ref:`Actions`.

.. code-block:: yaml

   - triggers:
     - on_deployment_create: {}
     - on_daemonset_update: {}
     actions:
     - my_first_action: {}
     - my_second_action: {}

For every incoming event, Robusta will run actions if any of the ``triggers`` match.

All the ``actions`` will be executed, according to the order specified in the configuration.

Execution order is the same as the configuration order. For example:

.. code-block:: yaml

   - triggers:  # playbook A
     - on_deployment_create: {}
     actions:
     - my_first_action: {}
   - triggers:  # playbook B
     - on_deployment_create: {}
     actions:
     - my_second_action: {}

On the example above, ``playbook A`` will run before ``playbook B``

Stop Processing
^^^^^^^^^^^^^^^^^^
Any action can :ref:`stop the processing flow <stop_processing>` if needed. No further actions will run.

This is how actions like :ref:`node_restart_silencer <node_restart_silencer>` work.

Only actions that appear **after** the current action will be stopped. This means, for example, that silencers must appear before other playbooks.
