.. admonition:: AlertManager config for sending alerts to Robusta

.. tab-set::

    .. tab-item:: kube-prometheus-stack (Prometheus Operator)

      Add the following to your `AlertManager's config Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_

      Do not apply in other ways, they all `have limitations <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_ and won't forward all alerts.

      .. code-block:: yaml

          receivers:
            - name: 'robusta'
              webhook_configs:
                - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts' # (2)
                  send_resolved: true # (4)
            - name: 'default-receiver'

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
            receiver: 'default-receiver'

      .. code-annotations::
        1. Put Robusta's route as the first route, to guarantee it receives alerts. If you can't do so, you must guarantee all previous routes set ``continue: true`` set.
        2. This assumes Robusta was installed in the ``default`` namespace, using a Helm release named ``robusta``.
            * If the namespace is ``foobar``, replace ``default`` with ``foobar``
            * If the Helm release is named ``robert`` then replace ``robusta`` with ``robert``
        3. Keep sending alerts to receivers defined after Robusta.
        4. Important, so Robusta knows when alerts are resolved.

    .. tab-item:: Other Prometheus Installations

      Add the following to your AlertManager configuration, wherever it is defined.

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
