Verify it Works
^^^^^^^^^^^^^^^^^^^

Send a dummy alert to AlertManager:

.. tab-set::

    .. tab-item:: Robusta CLI

        If you have the Robusta CLI installed, you can send a test alert using the following command:

        .. code-block:: bash

            robusta demo-alert

    .. tab-item:: Robusta UI

        In the Robusta UI, go to the "Clusters" tab, choose the right cluster and click "Simulate Alert".
        
        .. image:: /images/robusta-ui-simulate-alert-1.png
           :alt: Choose the cluster
           :width: 600
           :align: center

        Then 

        1. Check **Send alert with no resource**.
        2. Provide a name for the alert in the **Alert name (identifier)** field (e.g., "Testing Prod AlertManager").
        3. Select **Alert Manager** under the "Send alert to" section.
        4. Click the **Simulate Alert** button to send the test alert.

        .. image:: /images/robusta-ui-simulate-alert-2.png
           :alt: Send Test Alert
           :width: 600
           :align: center

If everything is setup properly, this alert will reach Robusta. It will show up in the Robusta UI, Slack, and other configured sinks.

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
    :ref:`customize this mapping <Relabel Prometheus Alerts>` to fit your environment.
