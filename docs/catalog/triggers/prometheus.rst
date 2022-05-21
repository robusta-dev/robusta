.. _on_prometheus_alert:

Prometheus and AlertManager
#############################

Robusta can run actions in response to any Prometheus alert. For example:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: HostHighCpuLoad
      actions:
      - node_bash_enricher:
         bash_command: ps aux

This will run the ``ps aux`` on the relevant node whenever a ``HostHighCpuLoad`` alert fires. The output will be
sent to the default sinks.

How it works
^^^^^^^^^^^^^^^^^

Relevant Kubernetes resources are loaded from the alert's metadata. Then Robusta actions are run with those resources
as input.

In the example above, the ``node_cpu_enricher`` receives the node on which the alert fired.

Limiting when on_prometheus_alert fires
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can limit when the automation runs by applying the following filters to ``on_prometheus_alert``:

.. pydantic-model:: robusta.integrations.prometheus.trigger.PrometheusAlertTrigger

Sending Alerts to Robusta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For Robusta to improve Prometheus alerts, it has to see those alerts. The setup depends on how you installed Prometheus.

Robusta's Embedded Prometheus
-----------------------------
If you installed Robusta's :ref:`Embedded Prometheus Stack` then no configuration is necessary.

Prometheus Operator
-----------------------
If you are using a Prometheus Operator that was **not**  externally to Robusta, you should define a `manually-managed secret <https://github.com/prometheus-operator/prometheus-operator/blob/master/Documentation/user-guides/alerting.md#manually-managed-secret>`_
that sends alerts to Robusta by webhook.

Follow the `instructions in the Prometheus Operator documentation <https://github.com/prometheus-operator/prometheus-operator/blob/master/Documentation/user-guides/alerting.md#manually-managed-secret>`_, using the following configuration for alertmanager.yaml:

.. admonition:: alertmanager.yaml

    .. code-block:: yaml

        receivers:
          - name: 'webhook'
            webhook_configs:
              - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts'
                send_resolved: true

An alternative is to configure an AlertmanagerConfig CRD, but this is **not** recommended as it `will only forward alerts from one namespace <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.

Other In-Cluster Prometheus Installations
------------------------------------------
If you installed Prometheus in some other way, you will need to manually edit the `AlertManager configuration <https://prometheus.io/docs/alerting/latest/configuration/>`_ as follows:

.. admonition:: alertmanager.yaml

    .. code-block:: yaml

        receivers:
          - name: 'webhook'
            webhook_configs:
              - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts'
                send_resolved: true

This file should be saved in different locations depending on your AlertManager setup.

Out-of-cluster Prometheus Installations
-----------------------------------------

If AlertManager is located outside of your Kubernetes cluster then a few more steps are necessary:

1. Enable two-way interactivity in :ref:`Robusta's configuration <Configuration Guide>` by setting ``disableCloudRouting: false``
2. Make sure that your alerts contain a label named ``cluster_name`` which matches the :ref:`cluster_name defined in Robusta's configuration <Mandatory global config>`. This is necessary so that the Robusta cloud knows which cluster to forward events to.
3. Add an http_config to AlertManager's configuration to configure security features.

.. admonition:: External AlertManager configuration

    .. code-block:: yaml

        receivers:
          - name: 'webhook'
            webhook_configs:
              - url: 'https://api.robusta.dev/integrations/generic/alertmanager'
                http_config:
                  authorization:
                    credentials: TOKEN
                send_resolved: true

The `TOKEN` format is: `ACCOUNT_ID SIGNING_KEY`

Developing actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is a custom playbook action that runs on Prometheus alerts:

.. admonition:: Example Prometheus playbook

    .. code-block:: python

        @action
        def my_action(alert: PrometheusKubernetesAlert):
            print(f"The alert {alert.alert_name} fired on pod {alert.pod.metadata.name}")
            print(f"The pod has these processes:", alert.pod.exec("ps aux"))
            print(f"The pod has {len(alert.pod.spec.containers)} containers")


``alert.pod`` is a Kubernetes pod object. It will exist if the Prometheus alert had a ``pod`` label and the pod is alive
when the playbook runs. There are also ``node``, ``deployment``, and ``daemonset`` fields.
