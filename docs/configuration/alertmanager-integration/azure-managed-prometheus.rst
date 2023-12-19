Azure managed Prometheus
*************************

This guide walks you through integrating your Azure managed Prometheus with Robusta. You will need to configure two integrations: both a push integration and a pull integration.

Configure Push Integration
===============================

A push integration sends Azure Managed Prometheus alerts to Robusta. To configure it:

1. Login to the Robusta UI and navigate to the ``Settings`` > ``Advanced`` tab.
2. In the Azure Webhook section click ``Generate URL`` and save the generated url.
3. Login to the Microsoft Azure Portal, go to ``Alerts`` > ``Action groups``
4. Create a new action group, or edit an existing one.
5. Under the `Actions` tabs (**not** the Notifications tab) add a ``Webhook`` and copy the url from step 2, into the URI input. Make sure to select ``Enable the common alert schema``.

.. details:: Why do I see a banner in the UI that "Alerts won't show up"?
    :class: warning

    This notification is displayed until the first alert to Robusta.

Configure Pull Integration
===============================

A pull integration lets Robusta pull metrics from Azure Managed Prometheus.

This can be configured either of two ways:

.. details:: Option #1: Create an Azure Active Directory authentication app

  **Pros:**
    - Quick setup. Just need to create an app, get the credentials and add them to the manifests
    - Other pods can't use the Service Principal without having the secret
  **Cons:**
    - Requires a service principal (Azure AD permission)
    - Need the client secret in the kubernetes manifests
    - Client secret expires, you need to manage its rotation

.. details:: Option #2: Use kubelet Managed Identity

  **Pros:**
    * Quick setup. Get the Managed Identity Client ID and add them to the manifests
    * No need to manage secrets. Removing the password element decreases the risk of the credentials being compromised
  **Cons:**
    * Managed Identity is bound to the entire VMSS, which means that other pods can use it if they have the client ID

Retrieve the Azure Prometheus query endpoint
==============================================

Whichever method you choose, you will need an Azure Prometheus query endpoint:

1. Go to `Azure Monitor workspaces <https://portal.azure.com/#view/HubsExtension/BrowseResource/resourceType/microsoft.monitor%2Faccounts>`_ and choose your monitored workspace.
2. In your monitored workspace, `overview`, find the ``Query endpoint`` and copy it.
3. In your `generated_values.yaml` file add the query endpoint URL under ``globalConfig`` with a 443 port:

.. code-block:: yaml

  globalConfig: # this line should already exist
      prometheus_url: "<https://your-workspace.region.prometheus.monitor.azure.com>:443"

Option #1: Create an Azure authentication app
==============================================

Create an Azure authentication app and get credentials for Robusta to access Prometheus data:

1. Follow the Azure guide to `register an app with Azure Active Directory <https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/prometheus-self-managed-grafana-azure-active-directory#register-an-app-with-azure-active-directory>`_

2. In your generated_values.yaml file add environment variables from the previous step.

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

3. Complete the step `allow your app access to your workspace <https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/prometheus-self-managed-grafana-azure-active-directory#allow-your-app-access-to-your-workspace>`_, so your app can query data from your Azure Monitor workspace.

Option #2: Use Kubelet's Managed Identity
==============================================

Instead of creating an Azure authentication app, you can use kubelet's Managed Identity to access Prometheus.
(As a variation on this, you can also create a new User Assigned Managed Identity and bind it to the underlying VMSS.)

1. Get the AKS kubelet's Managed Identity Client ID:

.. code-block:: bash

  az aks show -g <resource-group> -n <cluster-name> --query identityProfile.kubeletidentity.clientId -o tsv

2. In your generated_values.yaml file add the following environment variables from the previous step.

.. code-block:: yaml

  runner:
    additional_env_vars:
    - name: PROMETHEUS_SSL_ENABLED
      value: "true"
    - name: AZURE_USE_MANAGED_ID
      value: "true"
    - name: AZURE_CLIENT_ID
      value: "<your-client-id>"
    - name: AZURE_TENANT_ID
      value: "<your-tenant-id>"

3. Give access to your Managed Identity on your workspace:

   a. Open the Access Control (IAM) page for your Azure Monitor workspace in the Azure portal.
   b. Select Add role assignment.
   c. Select Monitoring Data Reader and select Next.
   d. For Assign access to, select Managed identity.
   e. Select + Select members.
   f. Select the Managed Identity you got from step 1.
   g. Select Review + assign to save the configuration.


Optional Settings
==================

**Prometheus flags checks**

.. include:: ./_prometheus_flags_check.rst
