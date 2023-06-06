In-cluster Prometheus
****************************************

For Robusta to :ref:`improve Prometheus alerts<Enhanced Prometheus Alerts>`, Robusta has to first receive those alerts from AlertManager.


**If you installed Robusta's** :ref:`Embedded Prometheus Stack` **then no configuration is necessary.**

If AlertManager is located inside your Kubernetes cluster, you must

1. Configure Push integration to receive alerts.
2. Configure Pull integration for Robusta to reach out and pull in graphs from Prometheus, to define alert silences etc.

Configure Push Integration
============================
To configure Prometheus to send alerts to Robusta, add two settings to AlertManager:

1. A webhook receiver for Robusta
2. A route for the webhook receiver you added

.. 3. Adding :ref:`Prometheus discovery URL<Setting up a custom Prometheus, AlertManager, and Grafana>` to Robusta

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

.. include:: ./_additional_settings.rst