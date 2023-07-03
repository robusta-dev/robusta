To test this, we can send a dummy alert to AlertManager:

.. code-block:: bash

    robusta demo-alert

If everything was configured properly, AlertManager will push this alert to Robusta. The alert will show up in the Robusta UI, Slack, and any other configured sinks.

.. details:: I configured AlertManager, but I'm still not receiving alerts?
    :class: warning

    Try sending a demo-alert as described above, and check the AlertManager logs for errors. Or reach out to us on `Slack <https://bit.ly/robusta-slack>`_.

    Other places to look for errors
        1. kube-prometheus-operator logs
        2. AlertManager UI status page
