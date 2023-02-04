Sending Alerts to Robusta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For Robusta to improve Prometheus alerts, it has to see those alerts.

To set it up, you'll have to configure an AlertManager ``receiver`` and ``route``.

If you installed Robusta's :ref:`Embedded Prometheus Stack` then no configuration is necessary.
For all other setups, read on!

General Instructions
======================
For Prometheus to send alerts to Robusta, add the following to AlertManager's config file.
The exact method of doing so will depend on your setup. (See below.)

.. admonition:: AlertManager config for sending alerts to Robusta

    .. code-block:: yaml

        receivers:
          - name: 'robusta'
            webhook_configs:
              # the following line assumes that Robusta was installed in the `default` namespace.
              # if you installed Robusta in a different namespace, replace `default` with the correct namespace
              - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts'
                send_resolved: true

        route:
          routes:
          - receiver: 'robusta'
            match_re:
              severity: 'info|warn|error|critical'
            repeat_interval: 4h
            continue: true

.. admonition:: Common Mistakes

    1. The ``default`` in the webhook_config url, is the namespace robusta is installed on. If you installed Robusta on a different namespace, update the url accordingly.
    2. Make sure the Robusta ``route`` is the first ``route`` defined. If it isn't the first route, it might not receive alerts. When a ``route`` is matched, the alert will not be sent to the following routes, unless the ``route`` is configured with ``continue: true``.

After you configure AlertManager, you can test it works properly, by creating a demo alert:

.. code-block:: bash

    robusta demo-alert

You should see the demo alert in the Robusta UI, Slack, etc within a few minutes

.. admonition:: Why do I still see a banner in the Robusta UI that "Alerts won't show up"?
    :class: warning

    This notification can remain for a few minutes after configuring AlertManager.
    It will disappear once the first alert arrives in Robusta.

Specific Instructions
======================

Here are instructions for configuring AlertManager in specific setups. Don't see your setup? Just follow the
:ref:`General Instructions` above.

kube-prometheus-stack and Prometheus Operator
------------------------------------------------

If you installed kube-prometheus-stack or Prometheus Operator **by yourself** (not via Robusta) then tell
AlertManager about Robusta using a `manually-managed secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#using-a-kubernetes-secret>`_.

Copy the config :ref:`above <General Instructions>` and place it in the appropriate secret.

The Prometheus Operator will pass this secret to AlertManager. AlertManager will then push alerts to Robusta by webhook.

.. admonition:: Why use a secret instead of editing AlertManagerConfig?

    In theory, you can configure an AlertmanagerConfig instead of using a secret. However, this is **not** recommended.
    It `will only forward alerts from one namespace <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.

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
                    # Replace <TOKEN> with a string in the format `<ACCOUNT_ID> <SIGNING_KEY>`
                    credentials: <TOKEN>
                send_resolved: true

        route:
          routes:
          - receiver: 'robusta'
            match_re:
              severity: 'info|warn|error|critical'
            repeat_interval: 4h
            continue: true

Robusta's Embedded Prometheus
-----------------------------
If you installed Robusta's :ref:`Embedded Prometheus Stack` then no configuration is necessary.

Related Robusta Settings
====================================

Below are additional Robusta settings related to Prometheus, AlertManager, and Grafana.

Setting up a custom Prometheus, AlertManager, and Grafana
-----------------------------------------------------------

If you followed the instructions on this page, Prometheus and AlertManager will know about Robusta, but Robusta might not know about them!

For certain Robusta features to work, Robusta needs to reach out to Prometheus and pull in extra information. This needs
to be configured **in addition** to updating AlertManager's configuration.

That said, most users won't need to set this up. Robusta can usually figure out on it's own where Prometheus and
other services are located. But if the auto-discovery isn't working, you can tell Robusta yourself where to find them:

Add the following to ``generated_values.yaml`` and :ref:`update Robusta <Helm Upgrade>`.

.. code-block:: yaml

  # these lines should already exist in generated_values.yaml
  global_config:
      cluster_name: <your cluster name>
      ...
      # add the lines below
      alertmanager_url: ""
      grafana_url: ""
      prometheus_url: "http://PROMETHEUS_SERVICE_NAME.monitoring.svc.cluster.local:9090"


Alerts silencing
-------------------

Robusta enables silencing AlertManager alerts directly from your notification channels (sinks).

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
