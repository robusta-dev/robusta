kube-prometheus-stack and Prometheus Operator
*********************************************

If you installed kube-prometheus-stack or the Prometheus Operator **by yourself** (not via Robusta) then tell
AlertManager about Robusta using a `Kubernetes Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_.
The Prometheus Operator will pass this secret to AlertManager, which will then push alerts to Robusta by webhook.

To configure the secret, copy this configuration and place it in the appropriate secret.

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

.. admonition:: Why use a secret instead of editing AlertManagerConfig?

    In theory, you can configure an AlertmanagerConfig instead of using a secret. However, this is **not** recommended.
    It `will only forward alerts from one namespace <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.

.. include:: ./_additional_settings.rst