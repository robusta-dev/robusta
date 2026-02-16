AlertManager - external
************************

Follow this guide to connect Robusta to a central Prometheus (e.g. Thanos/Mimir), running outside the cluster monitored by Robusta.

.. note::

    **Using Grafana Cloud?** For Grafana Cloud with Mimir, see the dedicated guide: :doc:`grafana-cloud`

You will need to configure two integrations: one to send alerts to Robusta and another to let Robusta query metrics and create silences.

Send Alerts to Robusta
==============================

This integration lets your central Prometheus send alerts to Robusta, as if they were in the same cluster:

1. Verify that all alerts contain a label named ``cluster_name`` or ``cluster``, matching the :ref:`cluster_name defined in Robusta's configuration <Global Config>`. This is necessary to identify which robusta-runner should receive alerts.
2. Edit the configuration for your centralized AlertManager:

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

Send Alerts to Robusta with API Key
======================================

If you are using a third-party AlertManager and want to give it separate credentials (instead of using the signing key from ``generated_values.yaml``), you can create a dedicated API key in the Robusta UI.

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

1. In the Robusta UI, go to **Settings → API Keys**.
2. Click **New API Key**, select **Alerts: Write** permissions, and **Save**.
3. Copy the generated API key.
4. Find your ``account_id``:

   - In your **generated_values.yaml** file (from installation), or
   - In the Robusta UI under **Settings → Workspace**.

5. Edit the configuration for your AlertManager, using the API key in place of the signing key:

.. admonition:: alertmanager.yaml

    .. code-block:: yaml

        receivers:
          - name: 'robusta'
            webhook_configs:
              - url: 'https://api.robusta.dev/integrations/generic/alertmanager'
                http_config:
                  authorization:
                    # Replace <ACCOUNT_ID> with your Robusta account ID
                    # Replace <API_KEY> with the API key you created above
                    credentials: '<ACCOUNT_ID> <API_KEY>'
                send_resolved: true

        route:
          routes:
          - receiver: 'robusta'
            group_by: [ '...' ]
            group_wait: 1s
            group_interval: 1s
            matchers:
              - severity =~ ".*"
            repeat_interval: 4h
            continue: true

.. include:: ./_testing_integration.rst

.. include:: ./_pull_integration.rst

Filtering Prometheus Queries by Cluster
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the same external Prometheus is used for many clusters, you will want to add a cluster name to all queries.

You can do so with the ``prometheus_url_query_string`` parameter, shown below:

.. code-block:: yaml

  globalConfig:
    # Additional query string parameters to be appended to the Prometheus connection URL (optional)
    prometheus_url_query_string: "cluster=prod1&x=y"