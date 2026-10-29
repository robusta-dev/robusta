Verify it Works
^^^^^^^^^^^^^^^^^^^

Send a dummy alert to AlertManager:

.. tab-set::

    .. tab-item:: Robusta CLI

        If you have the Robusta CLI installed, you can send a test alert using the following command:

        .. code-block:: bash

            robusta demo-alert


If everything is setup properly, this alert will reach Robusta. It will show up in Slack and other configured sinks.

.. note::

    It might take a few minutes for the alert to arrive due to AlertManager's `group_wait` and `group_interval` settings. More info `here <https://prometheus.io/docs/alerting/latest/configuration/#:~:text=How%20long%20to%20wait%20before%20sending%20a%20notification%20about%20new%20alerts%20that%0A%23%20are%20added%20to%20a%20group%20of%20alerts%20for%20which%20an%20initial%20notification%20has%0A%23%20already%20been%20sent>`_.

.. details:: I configured AlertManager, but I'm not receiving alerts?
    :class: warning

    Try sending a demo-alert as described above. If nothing arrives, check:

    1. AlertManager UI status page - verify that your config was picked up
    2. kube-prometheus-operator logs (if relevant)
    3. AlertManager logs

    Reach out on `Slack <https://bit.ly/robusta-slack>`_ for assistance.

.. details:: Robusta isn't mapping alerts to Kubernetes resources
    :class: warning

    Robusta enriches alerts with Kubernetes and log data using Prometheus labels for mapping.
    Standard label names are used by default. If your setup differs, you can
    `customize this mapping </configuration/alertmanager-integration/customize-labels-priorities.html>`_ to fit your environment.
