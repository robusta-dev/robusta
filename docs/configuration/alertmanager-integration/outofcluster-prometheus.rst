Out-of-cluster Prometheus
**************************************
This guide walks you through integrating an out-of-cluster Prometheus with Robusta. You will need to configure two integrations: both a push integration and a pull integration.

Configure Push Integration
==============================

1. Enable two-way interactivity by setting ``disableCloudRouting: false`` in the ``generated_values.yaml`` file.
2. Make sure that your alerts contain a label named ``cluster_name`` which matches the :ref:`cluster_name defined in Robusta's configuration <Global Config>`. This is necessary so that the Robusta cloud knows which cluster to forward events to.
3. Add the following configuration to your AlertManager:

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
                send_resolved: true # (3)

        route: # (1)
          routes:
          - receiver: 'robusta'
            group_by: [ '...' ]
            group_wait: 1s
            group_interval: 1s
            matchers:
              - severity =~ ".*"
            repeat_interval: 4h
            continue: true # (2)

    .. code-annotations::
      1. Make sure the Robusta ``route`` is the first ``route`` defined. If it isn't the first route, it might not receive alerts. When a ``route`` is matched, the alert will not be sent to following routes, unless the ``route`` is configured with ``continue: true``.
      2. Ensures that alerts continue to be sent even after a match is found
      3. Enables sending resolved alerts to Robusta

.. include:: ./_testing_integration.rst

.. include:: ./_pull_integration.rst

.. include:: ./_additional_settings.rst
