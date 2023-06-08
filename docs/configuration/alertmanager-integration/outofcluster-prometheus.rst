Out-of-cluster Prometheus
**************************************

This guide walks you through configuring your out of cluster Prometheus to push alerts to Robusta and also configuring Robusta to pull additional data when needed.

Configure Push Integration
==============================

1. Enable two-way interactivity by setting ``disableCloudRouting: false``in :ref:`Robusta's configuration <Configuration Overview>`.
2. Make sure that your alerts contain a label named ``cluster_name`` which matches the :ref:`cluster_name defined in Robusta's configuration <Global Config>`. This is necessary so that the Robusta cloud knows which cluster to forward events to.
3. Add the following configuration to you AlertManager:

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

        route: # (1)
          routes:
          - receiver: 'robusta'
            matchers:
              - severity =~ "info|warn|error|critical"
            repeat_interval: 4h
            continue: true

    .. code-annotations::
      1. Make sure the Robusta ``route`` is the first ``route`` defined. If it isn't the first route, it might not receive alerts. When a ``route`` is matched, the alert will not be sent to following routes, unless the ``route`` is configured with ``continue: true``.

After you configure AlertManager, you can test it works properly, by creating a demo alert. Run:

.. code-block:: bash

    robusta demo-alert

Within a few minutes, you should see the demo alert in the Robusta UI, Slack, and any other sinks you configured.

.. details:: Why do I see a banner in the UI that "Alerts won't show up"?
    :class: warning

    This notification is displayed until AlertManager sends the first alert to Robusta.

.. include:: ./_pull_integration.rst

.. include:: ./_additional_settings.rst