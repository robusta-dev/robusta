.. admonition:: AlertManager config for sending alerts to Robusta

    .. code-block:: yaml

        receivers:
          - name: 'robusta'
            webhook_configs:
              - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts' # (2)
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
      2. The following line assumes that Robusta was installed in the `default` namespace.
          * If you installed Robusta in a different namespace, replace `default` with the correct namespace
          * Likewise, if you named your Helm release ``robert`` then replace ``robusta`` with ``robert``
