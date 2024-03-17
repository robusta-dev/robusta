.. admonition:: AlertManager config for sending alerts to Robusta

  .. tab-set::

      .. tab-item:: kube-prometheus-stack (Prometheus Operator)

        Add the following to your `AlertManager's config Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_

        Do not apply in other ways, they all `have limitations <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_ and won't forward all alerts.

        .. code-block:: yaml

            receivers:
              - name: 'robusta'
                webhook_configs:
                  - url: 'http://<helm-release-name>-runner.<namespace>.svc.cluster.local/api/alerts'
                    send_resolved: true # (3)
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
                  continue: true # (2)
              receiver: 'default-receiver'

        .. code-annotations::
          1. Put Robusta's route as the first route, to guarantee it receives alerts. If you can't do so, you must guarantee all previous routes set ``continue: true`` set.
          2. Keep sending alerts to receivers defined after Robusta.
          3. Important, so Robusta knows when alerts are resolved.

      .. tab-item:: Other Prometheus Installations

        Add the following to your AlertManager configuration, wherever it is defined.

        .. code-block:: yaml

            receivers:
              - name: 'robusta'
                webhook_configs:
                  - url: 'http://<helm-release-name>-runner.<namespace>.svc.cluster.local/api/alerts'
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
          1. Put Robusta's route as the first route, to guarantee it receives alerts. If you can't do so, you must guarantee all previous routes set ``continue: true`` set.
          2. Keep sending alerts to receivers defined after Robusta.
          3. Important, so Robusta knows when alerts are resolved.
