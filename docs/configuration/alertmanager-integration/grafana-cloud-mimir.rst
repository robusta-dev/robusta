Grafana Cloud (Mimir)
********************************

This guide walks you through integrating Robusta with Grafana Cloud, enabling both the Robusta runner and Holmes to query metrics from Mimir and receive alerts from Grafana Cloud AlertManager.

Prerequisites
=============

Before starting, ensure you have:

* A Grafana Cloud account with a configured instance
* Prometheus and AlertManager datasources configured in Grafana Cloud
* Access to create service accounts and API tokens in Grafana Cloud
* Your Robusta ``account_id`` and ``signing_key`` from ``generated_values.yaml``

Step 1: Gather Grafana Cloud Information
=========================================

Find Your Grafana Instance Details
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Log into your Grafana Cloud portal
2. Note your Grafana instance URL (e.g., ``https://YOUR-INSTANCE.grafana.net``)

Create API Keys
^^^^^^^^^^^^^^^

You'll need credentials for Grafana API Access (used by both Robusta Runner and Holmes):

1. Go to **Administration → Service accounts**
2. Create a new service account named "robusta-integration"
3. Generate a service account token
4. Save the token (starts with ``glsa_``)

Find Your Cluster Name
^^^^^^^^^^^^^^^^^^^^^^

If your grafana setup covers  multiple clusters, the cluster name is required and used to 
identify your specific cluster in Prometheus queries:

1. Go to Grafana → Explore
2. Run query: ``up{cluster!=""}``
3. Check the cluster label values
4. This value will be set to ``cluster_name`` in your ``generated_values.yaml``

Find Datasource UIDs
^^^^^^^^^^^^^^^^^^^^

Using the Grafana API, list your datasources:

.. code-block:: bash

    curl -H "Authorization: Bearer YOUR_GLSA_TOKEN" \
      "https://YOUR-INSTANCE.grafana.net/api/datasources" | jq

Note the UID for Prometheus datasource UID (typically ``grafanacloud-prom``)

Step 2: Configure Robusta Runner
=================================

Update Robusta Values
^^^^^^^^^^^^^^^^^^^^^

Add the following to your ``generated_values.yaml``:

.. code-block:: yaml

    globalConfig:
      # Your Robusta account details (should already exist)
      account_id: YOUR_ROBUSTA_ACCOUNT_ID
      signing_key: YOUR_ROBUSTA_SIGNING_KEY
      
      # Grafana Cloud Prometheus Configuration (via proxy)
      prometheus_url: https://YOUR-INSTANCE.grafana.net/api/datasources/proxy/uid/PROMETHEUS_DATASOURCE_UID
      prometheus_auth: Bearer YOUR_GLSA_TOKEN
      
      # Grafana Cloud AlertManager Configuration 
      alertmanager_url: https://YOUR-INSTANCE.grafana.net
      alertmanager_flavor: grafana
      alertmanager_auth: Bearer YOUR_GLSA_TOKEN
      
      # Grafana API Key for enrichments
      grafana_api_key: YOUR_GLSA_TOKEN
      
      # Cluster identification (required)
      cluster_name: YOUR_CLUSTER_NAME

.. note::

    The ``prometheus_url`` uses Grafana's proxy endpoint format which handles authentication and routing to Mimir automatically.

Apply Configuration
^^^^^^^^^^^^^^^^^^^

Apply the configuration changes:

.. code-block:: bash

    helm upgrade robusta robusta/robusta -f generated_values.yaml -n default

Restart Robusta Runner
^^^^^^^^^^^^^^^^^^^^^^

Ensure the changes take effect:

.. code-block:: bash

    kubectl rollout restart deployment/robusta-runner -n default

Step 3: Configure Holmes Prometheus Toolset
============================================

Holmes requires additional configuration to work with Grafana Cloud's Mimir backend.

For detailed instructions on configuring Holmes with Grafana Cloud, see the **Grafana Cloud (Mimir) Configuration** section in :doc:`/configuration/holmesgpt/toolsets/prometheus`.

The key configuration points for Grafana Cloud are:

* Use the proxy endpoint URL format: ``https://YOUR-INSTANCE.grafana.net/api/datasources/proxy/uid/PROMETHEUS_DATASOURCE_UID``
* Set ``fetch_labels_with_labels_api: false`` (important for Mimir compatibility)
* Set ``fetch_metadata_with_series_api: true`` (important for Mimir compatibility)
* Use Bearer authentication with your service account token

After updating your ``generated_values.yaml`` with the Holmes configuration, apply the changes:

.. code-block:: bash

    helm upgrade robusta robusta/robusta -f generated_values.yaml -n default
    kubectl rollout restart deployment/robusta-holmes -n default

Step 4: Configure Alert Routing (Optional)
===========================================

To send alerts from Grafana Cloud to Robusta's timeline, follow the alert configuration steps in :doc:`grafana-alert-manager`.

The key differences for Grafana Cloud are:

1. Use your Grafana Cloud instance URL
2. Use the service account token (``glsa_`` token) for authentication
3. Ensure your alerts include the ``cluster`` label matching your configured ``cluster_name``

Verification
============

Verify Metrics Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Open any application in the Robusta UI
2. Check if CPU and memory graphs are displayed
3. If graphs are shown, the metrics integration is working correctly

Verify Holmes Integration
^^^^^^^^^^^^^^^^^^^^^^^^^

1. Trigger a test alert or wait for an actual alert
2. In the Robusta UI, click on "Investigate with Holmes"
3. Verify that Holmes can query metrics and provide analysis

Troubleshooting
===============

Common Issues
^^^^^^^^^^^^^

**Metrics not showing in Robusta UI:**

* Verify the ``prometheus_url`` includes the correct datasource UID
* Check that the service account token has not expired
* Ensure the token has appropriate permissions to query metrics

**Holmes unable to query metrics:**

* Verify ``fetch_metadata_with_series_api`` is set to ``true``
* Check that the Holmes deployment has restarted after configuration changes
* Review Holmes logs for authentication errors: ``kubectl logs -n default deployment/robusta-holmes``

**Authentication errors:**

* Regenerate the service account token if expired
* Ensure the token is correctly formatted with ``Bearer `` prefix
* Verify the token has the necessary permissions in Grafana Cloud

Additional Resources
====================

* :doc:`grafana-alert-manager` - For configuring Grafana alerts
* :doc:`/configuration/holmesgpt/toolsets/prometheus` - For advanced Holmes configuration
* `Grafana Cloud Documentation <https://grafana.com/docs/grafana-cloud/>`_