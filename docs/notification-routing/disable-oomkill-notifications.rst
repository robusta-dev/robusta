Disable "OOMKill" Notifications
===================================

Configure Robusta to not send OOMKill notifications by disabling the built-in OOMKill playbook. 

.. code-block:: yaml

    disabledPlaybooks:
    - PodOOMKill

Similarly you can to disable any built-in notification using the name of the playbook. Find all the built-in playbooks `here <https://github.com/robusta-dev/robusta/blob/master/helm/robusta/values.yaml#L113>`_ and `here <https://github.com/robusta-dev/robusta/blob/master/helm/robusta/values.yaml#L169>`_