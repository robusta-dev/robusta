Remediate Alerts
===================

TODO

For example, we can write annotations to Grafana when deployments update:

.. code-block::

    - triggers:
      - on_deployment_update:
          name_prefix: my-app-name
          namespace_prefix: ns1
          labels_selector: app=my-app
      actions:
      - add_deployment_lines_to_grafana:
          grafana_url: ....

.. code-block::

    customPlaybooks:
    - triggers:
      - on_deployment_update:
          name_prefix: MyApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_api_key: grafana_key_goes_here
          grafana_dashboard_uid: id_for_dashboard1
          grafana_url: http://grafana.namespace.svc
      sinks:
      - "main_slack_sink"

..     .. tab-item:: Event Correlation
..         .. admonition:: Show application updates in Grafana to correlate them with error spikes
..             .. image:: /images/grafana-deployment-enrichment.png
..               :width: 400
..               :align: center
