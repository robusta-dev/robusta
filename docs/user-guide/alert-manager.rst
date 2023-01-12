Sending Alerts to Robusta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For Robusta to improve Prometheus alerts, it has to see those alerts.

To set it up, you'll have to configure an AlertManager ``receiver`` and a ``route`` that routes alerts to that ``receiver`` in your existing prometheus setup.

The setup depends on how you installed Prometheus.


Robusta's Embedded Prometheus
-----------------------------
If you installed Robusta's :ref:`Embedded Prometheus Stack` then no configuration is necessary.

AlertManager receiver and route definition
--------------------------------------------

Add this snippet to your Prometheus AlertManager **values.yaml** file. 

.. admonition:: Robusta receiver and route

    .. code-block:: yaml

        receivers:
          - name: 'robusta'
            webhook_configs:
              - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts'
                send_resolved: true
        route:
          routes:
          - receiver: 'robusta'
            match_re:
              severity: 'info|warn|error|critical'
            repeat_interval: 4h
            continue: true

    .. note::

      The ``default`` in the webhook_config url, is the namespace robusta is installed on. If you installed Robusta on a different namespace, update the url accordingly.

    .. note::

      When a ``route`` is matched, the alert will not be sent to the following routes, unless the ``route`` is configured with ``continue: true``
      Make sure the Robusta ``route`` is the first ``route`` defined.


After you configured the ``receiver`` and ``route``, you can test it works properly, by creating a demo alert on AlertManager:

.. code-block:: bash

    robusta demo-alert

You should see the demo alert, in the Robusta UI, Slack, or any other configured ``sink`` within a few minutes

.. admonition:: "Alerts won't show up" UI notification
    :class: warning

    The notification is displayed until the first alert is sent from AlertManager to Robusta.

Setting up custom services in Robusta
------------------------------------
Add custom AlertManager, Grafana or Prometheus in ``generated_values.yaml``. 

.. code-block:: yaml

  global_config:
  cluster_name: test-cluster
  ...
  alertmanager_url: ""
  grafana_url: ""
  prometheus_url: "http://PROMETHEUS_SERVICE_NAME.monitoring.svc.cluster.local:9090"

Prometheus Operator
-----------------------
If you are using a Prometheus Operator that was **not** installed with Robusta, you should define a `manually-managed secret <https://github.com/prometheus-operator/prometheus-operator/blob/master/Documentation/user-guides/alerting.md#manually-managed-secret>`_
that sends alerts to Robusta by webhook.

Follow the `instructions in the Prometheus Operator documentation <https://github.com/prometheus-operator/prometheus-operator/blob/master/Documentation/user-guides/alerting.md#manually-managed-secret>`_, using the above configuration for alertmanager.yaml.

An alternative is to configure an AlertmanagerConfig CRD, but this is **not** recommended as it `will only forward alerts from one namespace <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.

Other In-Cluster Prometheus Installations
------------------------------------------
If you installed Prometheus in some other way, you will need to manually edit the `AlertManager configuration <https://prometheus.io/docs/alerting/latest/configuration/>`_ and add the above configuration.

This file should be saved in different locations depending on your AlertManager setup.

Out-of-cluster Prometheus Installations
-----------------------------------------

If AlertManager is located outside of your Kubernetes cluster then a few more steps are necessary:

1. Enable two-way interactivity in :ref:`Robusta's configuration <Configuration Guide>` by setting ``disableCloudRouting: false``
2. Make sure that your alerts contain a label named ``cluster_name`` which matches the :ref:`cluster_name defined in Robusta's configuration <Mandatory global config>`. This is necessary so that the Robusta cloud knows which cluster to forward events to.
3. Configure AlertManager as follows:

.. admonition:: alertmanager.yaml

    .. code-block:: yaml

        receivers:
          - name: 'robusta'
            webhook_configs:
              - url: 'https://api.robusta.dev/integrations/generic/alertmanager'
                http_config:
                  authorization:
                    credentials: TOKEN
                send_resolved: true

        route:
          routes:
          - receiver: 'robusta'
            match_re:
              severity: 'info|warn|error|critical'
            repeat_interval: 4h
            continue: true

The `TOKEN` format is: `ACCOUNT_ID SIGNING_KEY`


Alerts silencing
-----------------------------------------

Robusta enables silencing AlertManager alerts directly from your notification channels (Sinks)

By default, Robusta finds the AlertManager running on your cluster, and use it to create silences

Some users use the AlertManager embedded in Grafana

To create the silences using that AlertManager, add the following configuration to the ``globalConfig`` section in your ``generated_values.yaml`` file:

.. admonition:: generated_values.yaml

    .. code-block:: yaml

        globalConfig:
          grafana_api_key: <YOUR GRAFANA EDITOR API KEY>
          alertmanager_flavor: grafana

    .. note::

      The Grafana api key must have ``Editor`` permission in order to create silences
