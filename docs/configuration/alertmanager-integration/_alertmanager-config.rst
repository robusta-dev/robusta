.. admonition:: AlertManager config for sending alerts to Robusta

    .. code-block:: yaml

        receivers:
          - name: 'robusta'
            webhook_configs:
              - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts' # (2)
                send_resolved: true # (4)

        route: # (1)
          routes:
            - receiver: 'robusta'
              group_by: [ '...' ]
              group_wait: 1s
              group_interval: 1s
              matchers:
                - severity =~ ".*"
              repeat_interval: 4h
              continue: true # (3)

    .. code-annotations::
      1. Put Robusta's route as the first route, to guarantee it receives alerts. If you can't do so, you must guarantee all previous routes set ``continue: true`` set.
      2. This assumes Robusta was installed in the ``default`` namespace, using a Helm release named ``robusta``.
          * If the namespace is ``foobar``, replace ``default`` with ``foobar``
          * If the Helm release is named ``robert`` then replace ``robusta`` with ``robert``
      3. Keep sending alerts to receivers defined after Robusta.
      4. Important, so Robusta knows when alerts are resolved.
