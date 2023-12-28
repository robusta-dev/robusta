Centralized Prometheus
**************************************

Follow this guide to connect Robusta to a central Prometheus (e.g. Thanos/Mimir), running outside the cluster monitored by Robusta.

You will need to configure two integrations: a push integration and a pull integration. (Both are necessary.)

Configure Push Integration
==============================

A push integration lets your central Prometheus send alerts to Robusta, as if they were in the same cluster:

1. Enable cloud-routing of alerts by setting ``disableCloudRouting: false`` in ``generated_values.yaml``.
2. Verify that all alerts contain a label named ``cluster_name`` or ``cluster``, matching the :ref:`cluster_name defined in Robusta's configuration <Global Config>`. This is necessary to identify which robusta-runner should receive alerts.
3. Edit the configuration for your centralized AlertManager:

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

Filtering Prometheus Queries by Cluster
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the same centralized Prometheus is used for many clusters, you will want to add a cluster name to all queries.

You can do so with the ``prometheus_url_query_string`` parameter, shown below:

.. code-block:: yaml

  globalConfig:
    # Additional query string parameters to be appended to the Prometheus connection URL (optional)
    prometheus_url_query_string: "cluster=prod1&x=y"
