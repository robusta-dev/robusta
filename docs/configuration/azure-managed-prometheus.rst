Azure managed Prometheus
*************************

Sending Azure Alerts to Robusta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For Robusta to :ref:`improve Prometheus alerts<Enhanced Prometheus Alerts>`, Robusta has to first receive those alerts from Azure.

To configure Azure to send alerts to Robusta:

1. Login to the Robusta UI and navigate to the ``settings`` > ``advanced`` tab.
2. In the Azure Webhook section click ``Generate URL`` and save the generated url.
3. Login to the Microsoft Azure Portal, go to ``alerts`` > ``Action groups``
4. Create a new action group, or edit an existing one.
5. Under the `Actions` tabs (**not** the Notifications tab) add a ``Webhook`` and copy the url from step 2, into the URI input.
6. Make sure to select ``Enable the common alert schema``.

.. admonition:: Why do I see a banner in the UI that "Alerts won't show up"?
    :class: warning

    This notification is displayed until the first alert to Robusta.

Configure Robusta to use Azure managed Prometheus
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For certain features, Robusta needs to reach out to Prometheus so that Robusta can analyze and present Prometheus data.
In order to authenticate against the Azure managed Prometheus service, you have two options:
- Create an Azure Active Directory authentication app (Option #1)
  - Pros:
    - Quick setup. Just need to create an app, get the credentials and add them to the manifests
    - Other pods can't use the Service Principal without having the secret
  - Cons:
    - Requires a service principal (Azure AD permission)
    - Need the client secret in the kubernetes manifests
    - Client secret expires, you need to manage its rotation
- Use Kubelet's Managed Identity (Option #2)
  - Pros:
    - Quick setup. Get the Managed Identity Client ID and add them to the manifests
    - No need to manage secrets. Removing the password element decreases the risk of the credentials being compromised
  - Cons:
    - Managed Identity is bound to the whole VMSS, so other pods can use it if they know the client ID

Get the Azure prometheus query endpoint
=========================================

1. Go to `Azure Monitor workspaces <https://portal.azure.com/#view/HubsExtension/BrowseResource/resourceType/microsoft.monitor%2Faccounts>`_ and choose your monitored workspace.
2. In your monitored workspace, `overview`, find the ``Query endpoint`` and copy it.
3. In your `generated_values.yaml` file add the query endpoint url with a 443 port:

.. code-block:: yaml

  # this line should already exist
  globalConfig:
      prometheus_url: "<https://your-workspace.region.prometheus.monitor.azure.com>:443"

Option #1: Create an Azure authentication app
==============================================

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

Option #2: Use Kubelet's Managed Identity
==============================================

We will now use the Kubelet's Managed Identity so Robusta can access Prometheus data. Alternatively, you can create a new User Assigned Managed Identity and bind it to the underlying VMSS. This guide will use the Kubelet's Managed Identity.

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
   f. Select the Managed Identity you got from step 1
   g. Select Review + assign to save the configuration.
