Azure managed Prometheus
*************************

This guide walks you through configuring your Azure managed Prometheus to push alerts to Robusta and also configuring Robusta to pull additional data when needed.

Configure Push Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For Robusta to :ref:`improve Prometheus alerts<Enhanced Prometheus Alerts>`, Robusta has to first receive those alerts from Azure.

To configure Azure to send alerts to Robusta:

1. Login to the Robusta UI and navigate to the ``Settings`` > ``Advanced`` tab.
2. In the Azure Webhook section click ``Generate URL`` and save the generated url.
3. Login to the Microsoft Azure Portal, go to ``Alerts`` > ``Action groups``
4. Create a new action group, or edit an existing one.
5. Under the `Actions` tabs (**not** the Notifications tab) add a ``Webhook`` and copy the url from step 2, into the URI input. Make sure to select ``Enable the common alert schema``.

.. details:: Why do I see a banner in the UI that "Alerts won't show up"?
    :class: warning

    This notification is displayed until the first alert to Robusta.

Configure Pull Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For certain features, Robusta needs to reach out to Prometheus and pull in extra information.
In this section we will configure Robusta to query Prometheus and also register an Azure authentication app.

Retrieve the Azure Prometheus query endpoint
==============================================

1. Go to `Azure Monitor workspaces <https://portal.azure.com/#view/HubsExtension/BrowseResource/resourceType/microsoft.monitor%2Faccounts>`_ and chose your monitored workspace.
2. In your monitored workspace, `overview`, find the ``Query endpoint`` and copy it.
3. In your `generated_values.yaml` file add the query endpoint url under ``globalConfig`` with a 443 port:

.. code-block:: yaml

  globalConfig: # this line should already exist
      prometheus_url: "<https://your-workspace.region.prometheus.monitor.azure.com>:443"

Create an Azure authentication app
=====================================

We will now create an Azure authentication app and get the necesssary credentials so Robusta can access Prometheus data.

1. Follow this Azure guide to `Register an app with Azure Active Directory <https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/prometheus-self-managed-grafana-azure-active-directory#register-an-app-with-azure-active-directory>`_

2. In your generated_values.yaml file add the following environment variables from the previous step.

.. code-block:: yaml

  runner:
    additional_env_vars:
    - name: PROMETHEUS_SSL_ENABLED
      value: "true"
    - name: AZURE_CLIENT_ID
      value: "<your-client-id>"
    - name: AZURE_TENANT_ID
      value: "<your-tenant-id>"
    - name: AZURE_CLIENT_SECRET
      value: "<your-client-secret>"

3. Complete the `Allow your app access to your workspace <https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/prometheus-self-managed-grafana-azure-active-directory#allow-your-app-access-to-your-workspace>`_ step, so your app can query data from your Azure Monitor workspace.