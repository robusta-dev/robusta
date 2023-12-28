Verify it Works
^^^^^^^^^^^^^^^^^^^

Send a dummy alert to AlertManager:

.. code-block:: bash

    robusta demo-alert

If everything is setup properly, this alert will reach Robusta. It will show up in the Robusta UI, Slack, and other configured sinks.

.. details:: I configured AlertManager, but I'm not receiving alerts?
    :class: warning

    Try sending a demo-alert as described above. If nothing arrives, check:

    1. AlertManager logs
    2. kube-prometheus-operator logs (if relevant)
    3. AlertManager UI status page - verify that your config was picked up

    Reach out on `Slack <https://bit.ly/robusta-slack>`_ for assistance.

.. details:: Robusta isn't mapping alerts to Kubernetes resources
    :class: warning

    Robusta enriches alerts with Kubernetes and log data using Prometheus labels for mapping.
    Standard label names are used by default. If your setup differs, you can
    :ref:`customize this mapping <Relabel Prometheus Alerts>` to fit your environment.
