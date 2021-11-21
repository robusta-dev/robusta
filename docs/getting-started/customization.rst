Customizing Playbooks
##############################

Robusta needs rules to tell it what to do. These rules are called "playbooks".

Enabling a new playbook
------------------------

1. Enable the ``resource_babysitter`` playbook:

.. admonition:: generated_values.yaml

    .. code-block:: yaml

        customPlaybooks:
        - triggers:
            - on_deployment_update: {}
          actions:
            - resource_babysitter:
                fields_to_monitor: ["spec.replicas"]


This playbook monitors changes to deployments. You can see all the settings in the :ref:`playbook's documentation <resource_babysitter>`.

2. Perform an upgrade with Helm to apply the new configuration

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

Seeing your new config in action
----------------------------------

1. Scale one of your deployments:

.. code-block:: python

   kubectl scale --replicas NEW_REPLICAS_COUNT deployments/DEPLOYMENT_NAME


2. Check the slack channel you configured when installing Robusta:

.. admonition:: Example Slack Message

    .. image:: ../images/replicas_change.png
      :width: 600
      :align: center
