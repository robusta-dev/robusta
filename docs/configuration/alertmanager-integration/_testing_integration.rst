To test if everything was configured properly, send a dummy alert to AlertManager using the command below:

.. code-block:: bash

    robusta demo-alert

AlertManager will push this alert to Robusta. The alert will show up in the Robusta UI, Slack, and any other configured sinks.

.. details:: I configured AlertManager, but I'm still not receiving alerts?
    :class: warning

    Try sending a demo-alert as described above, and check the AlertManager logs for errors. You can also reach out to us on `Slack <https://bit.ly/robusta-slack>`_.

    Other places to look for errors
        1. Check the kube-prometheus-operator logs.
        2. Check the AlertManager UI status page for the added config.
