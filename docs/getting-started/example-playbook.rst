Example Playbook
##############################

Robusta needs rules to tell it what to do. These rules are called "playbooks".

On this page, we configure a new playbook that monitors deployments. It will notify in Slack every time the
number of replicas changes.

Enabling the playbook
------------------------

Playbooks are configured with the ``customPlaybooks`` helm value.

1. Add the following to ``generated_values.yaml``:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_deployment_update: {}
      actions:
        - resource_babysitter:
            fields_to_monitor: ["spec.replicas"]


2. Perform an upgrade with Helm to apply the new configuration

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml


Seeing the Playbook in action
----------------------------------

1. Scale one of your deployments:

.. code-block:: python

   kubectl scale --replicas NEW_REPLICAS_COUNT deployments/DEPLOYMENT_NAME

2. Check the slack channel you configured when installing Robusta:

.. image:: ../images/replicas_change.png
  :width: 600
  :align: center

If you setup the Robusta UI, it will appear in the timeline of all alerts and changes:

.. image:: ../images/ui-timeline.png
  :width: 600
  :align: center

You can click to see the diff:

.. image:: ../images/ui-diff.png
  :width: 600
  :align: center


How the playbook works
----------------------------------
Every playbook configuration has three parts.

triggers:
    We chose ``on_deployment_update`` so our playbook runs every time deployments are updated

actions:
    We chose :ref:`Resource babysitter` which is a builtin action. That action has a parameter ``fields_to_monitor``.

sinks:
    We didn't configure any sinks, so output is sent to the default sink. This is usually Slack and/or the `Robusta UI <https://home.robusta.dev/ui/>`_.

Further customization
------------------------
Try changing the configuration to monitors changes to a deployment\'s image tag.
