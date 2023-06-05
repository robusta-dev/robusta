Out-of-cluster Prometheus
**************************************

For Robusta to :ref:`improve Prometheus alerts<Enhanced Prometheus Alerts>`, Robusta has to first receive those alerts from AlertManager.


**If you installed Robusta's** :ref:`Embedded Prometheus Stack` **then no configuration is necessary.**

If AlertManager is located outside of your Kubernetes cluster, follow these steps:

Configure AlertManager:
===========================

1. Enable two-way interactivity in :ref:`Robusta's configuration <Configuration Overview>` by setting ``disableCloudRouting: false``
2. Make sure that your alerts contain a label named ``cluster_name`` which matches the :ref:`cluster_name defined in Robusta's configuration <Global Config>`. This is necessary so that the Robusta cloud knows which cluster to forward events to.
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