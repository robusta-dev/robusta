Azure managed Prometheus
*************************

Sending Azure Alerts to Robusta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For Robusta to :ref:`improve Prometheus alerts<Enhanced Prometheus Alerts>`, Robusta has to first receive those alerts from Azure.

To configure Azure to send alerts to Robusta:

1. Login to the Robusta UI and navigate to the ``settings`` > ``advanced`` tab.
2. In the Azure Webhook section click ``Generate URL`` and save the generated url.
3. Login to the Microsoft Azure Portal, go to ``alerts`` > ``Action groups``
4. Edit your action group, in the `Actions` section add a ``Webhook`` and copy the url from step 2, into the URI input.
5. Make sure the ``Enable the common alert schema`` option is active.

.. admonition:: Why do I see a banner in the UI that "Alerts won't show up"?
    :class: warning

    This notification is displayed until the first alert to Robusta.

Configure Robusta to use Azure managed Prometheus
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For certain features, Robusta needs to reach out to Prometheus and pull in extra information.
In this section we will Create an Azure Active Directory authentication app so that Robusta can analyze and present Prometheus data.

Get the Azure prometheus query endpoint
=========================================

1. Go to `Azure Monitor workspaces <https://portal.azure.com/#view/HubsExtension/BrowseResource/resourceType/microsoft.monitor%2Faccounts>`_ and chose your monitored workspace.
2. In your monitored workspace, `overview`, find the ``Query endpoint`` and copy it.
3. In your `generated_values.yaml` file add the query endpoint url with a 443 port:

.. code-block:: yaml

  # this line should already exist
  globalConfig:
      prometheus_url: "<https://your-workspace.region.prometheus.monitor.azure.com>:443"

Create an Azure authentication app
=====================================

We will now create an Azure authentication app and get the necesssary credentials so Robusta can access Prometheus data.

1. Follow this Azure guide to `Register an app with Azure Active Directory <https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/prometheus-self-managed-grafana-azure-active-directory#register-an-app-with-azure-active-directory>`_

2. In your generated_values.yaml file add the following environment variables from the previous step.

.. code-block:: yaml

  runner:
    additional_env_vars:
    - name: AZURE_CLIENT_ID
      value: "<your-client-id>"
    - name: AZURE_TENANT_ID
      value: "<your-tenant-id>"
    - name: "AZURE_CLIENT_SECRET"
      value: "<your-client-secret>"

3. Complete the `Allow your app access to your workspace <https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/prometheus-self-managed-grafana-azure-active-directory#allow-your-app-access-to-your-workspace>`_ step, so your app can query data from your Azure Monitor workspace.
