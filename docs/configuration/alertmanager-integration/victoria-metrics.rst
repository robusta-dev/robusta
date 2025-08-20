VictoriaMetrics Alerts
***********************

This guide shows how to send alerts from `VictoriaMetrics <https://victoriametrics.com/>`_ with Robusta.

For configuring metric querying from VictoriaMetrics, see :doc:`/configuration/metric-providers-victoria`.

Send Alerts to Robusta
============================

Add the following to your Victoria Metrics Alertmanager configuration (e.g., Helm values file or VMAlertmanagerConfig CRD):

.. code-block:: yaml

    receivers:
      - name: 'robusta'
      webhook_configs:
          - url: 'http://<ROBUSTA-HELM-RELEASE-NAME>-runner.<NAMESPACE>.svc.cluster.local/api/alerts'
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
    1. Put Robusta's route as the first route, to guarantee it receives alerts. If you can't do so, you must guarantee all previous routes has ``continue: true`` set.
    2. Keep sending alerts to receivers defined after Robusta.
    3. Important, so Robusta knows when alerts are resolved.


.. include:: ./_testing_integration.rst

Configure Metrics Querying
====================================

To enable Robusta to query metrics from VictoriaMetrics, see metrics provider :doc:`/configuration/metric-providers-victoria` configuration docs.