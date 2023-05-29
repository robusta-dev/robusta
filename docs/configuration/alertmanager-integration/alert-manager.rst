Integrating AlertManager
****************************************

For Robusta to :ref:`improve Prometheus alerts<Enhanced Prometheus Alerts>`, Robusta has to first receive those alerts from AlertManager.


**If you installed Robusta's** :ref:`Embedded Prometheus Stack` **then no configuration is necessary.**

For other setups, read on!


Prerequisites
===============

* AlertManager


General Instructions
======================
To configure Prometheus to send alerts to Robusta, add two settings to AlertManager:

1. A webhook receiver for Robusta
2. A route for the webhook receiver you added
3. Adding :ref:`Prometheus discovery URL<Setting up a custom Prometheus, AlertManager, and Grafana>` to Robusta

Below is an example AlertManager configuration. Depending on your setup, the exact file to edit may vary. (See below.)

.. admonition:: AlertManager config for sending alerts to Robusta

    .. code-block:: yaml

        receivers:
          - name: 'robusta'
            webhook_configs:
              # the following line assumes that Robusta was installed in the `default` namespace.
              # if you installed Robusta in a different namespace, replace `default` with the correct namespace
              # likewise, if you named your Helm release ``robert`` then replace ``robusta`` with ``robert``
              - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts'
                send_resolved: true

        route:
          routes:
            - receiver: 'robusta'
              matchers:
                - severity =~ "info|warn|error|critical"
              repeat_interval: 4h
              continue: true

.. admonition:: Common Mistakes

    1. Make sure the Robusta ``route`` is the first ``route`` defined. If it isn't the first route, it might not receive alerts. When a ``route`` is matched, the alert will not be sent to following routes, unless the ``route`` is configured with ``continue: true``.
    2. Tweak the settings accordingly if:
        * You installed Robusta in a namespace other than ``default``
        * You named Robusta's Helm release something other than ``robusta``

After you configure AlertManager, you can test it works properly, by creating a demo alert:

.. code-block:: bash

    robusta demo-alert

Within a few minutes, you should see the demo alert in the Robusta UI, Slack, and any other sinks you configured.

.. admonition:: Why do I see a banner in the UI that "Alerts won't show up"?
    :class: warning

    This notification is displayed until AlertManager sends the first alert to Robusta.

Specific Instructions
==============================

Here are instructions for configuring AlertManager in specific setups. Don't see your setup? Just follow the
:ref:`General Instructions` above.

kube-prometheus-stack and Prometheus Operator
=====================================================

If you installed kube-prometheus-stack or the Prometheus Operator **by yourself** (not via Robusta) then tell
AlertManager about Robusta using a `Kubernetes Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_.
The Prometheus Operator will pass this secret to AlertManager, which will then push alerts to Robusta by webhook.

To configure the secret, copy the configuration :ref:`here <General Instructions>` and place it in the appropriate secret.

.. admonition:: Why use a secret instead of editing AlertManagerConfig?

    In theory, you can configure an AlertmanagerConfig instead of using a secret. However, this is **not** recommended.
    It `will only forward alerts from one namespace <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.


Related Robusta Settings
==============================

Below are additional Robusta settings related to Prometheus, AlertManager, and Grafana.

Setting up a custom Prometheus, AlertManager, and Grafana
------------------------------------------------------------

If you followed the instructions on this page, Prometheus and AlertManager will know about Robusta, but Robusta might not know about them!

For certain features, Robusta needs to reach out to Prometheus and pull in extra information. This must
be configured **in addition** to updating AlertManager's configuration.

That said, most users won't need to set this up. Robusta can usually figure out where Prometheus and
other services are located. If the auto-discovery isn't working, you'll configure it manually.

Add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.

.. tab-set::

    .. tab-item:: Prometheus

        .. code-block:: yaml

          # this line should already exist
          globalConfig:
              # add the lines below
              alertmanager_url: ""
              grafana_url: ""
              prometheus_url: "http://PROMETHEUS_SERVICE_NAME.monitoring.svc.cluster.local:9090"


    .. tab-item:: VictoriaMetrics

        .. code-block:: yaml

          # this line should already exist
          globalConfig:
              # add the lines below
              alertmanager_url: ""
              grafana_url: ""
              prometheus_url: "http://VICTORIA_METRICS_SERVICE_NAME.monitoring.svc.cluster.local:8429"

.. include:: ../_additional_settings.rst