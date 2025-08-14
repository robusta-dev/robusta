Azure Managed Prometheus
========================

Configure Robusta to use Azure Monitor's managed Prometheus service.

Prerequisites
-------------

1. An Azure Monitor workspace with Prometheus enabled
2. Either an Azure AD Service Principal or Managed Identity configured

Quick Start
-----------

1. **Get your workspace query endpoint**:
   
   - Go to `Azure Monitor workspaces <https://portal.azure.com/#view/HubsExtension/BrowseResource/resourceType/microsoft.monitor%2Faccounts>`_
   - Select your workspace
   - Copy the **Query endpoint** from the Overview page

2. **Choose your authentication method** and configure Robusta:

.. tab-set::

   .. tab-item:: Service Principal
      :name: service-principal

      1. `Create a Service Principal <https://learn.microsoft.com/en-us/azure/azure-monitor/metrics/prometheus-api-promql#authentication>`_ (app registration)
      
      2. Add to ``generated_values.yaml``:

      .. code-block:: yaml

          globalConfig:
              prometheus_url: "https://your-workspace.region.prometheus.monitor.azure.com:443"
              check_prometheus_flags: false  # Required for Azure
              
          runner:
              additional_env_vars:
              - name: PROMETHEUS_SSL_ENABLED
                value: "true"
              - name: AZURE_CLIENT_ID
                value: "your-app-client-id"
              - name: AZURE_TENANT_ID
                value: "your-tenant-id"
              - name: AZURE_CLIENT_SECRET
                value: "your-client-secret"

      3. Grant your app access to the workspace (Monitoring Data Reader role)

      4. :ref:`Update Robusta <Simple Upgrade>` 


   .. tab-item:: Managed Identity
      :name: managed-identity

      1. Get your AKS kubelet's Managed Identity:

      .. code-block:: bash

          az aks show -g <resource-group> -n <cluster-name> \
              --query identityProfile.kubeletidentity.clientId -o tsv

      2. Add to ``generated_values.yaml``:

      .. code-block:: yaml

          globalConfig:
              prometheus_url: "https://your-workspace.region.prometheus.monitor.azure.com:443"
              check_prometheus_flags: false  # Required for Azure
              
          runner:
              additional_env_vars:
              - name: PROMETHEUS_SSL_ENABLED
                value: "true"
              - name: AZURE_USE_MANAGED_ID
                value: "true"
              - name: AZURE_CLIENT_ID
                value: "your-kubelet-client-id"
              - name: AZURE_TENANT_ID
                value: "your-tenant-id"

      3. Grant the Managed Identity access to your workspace:
         
         - Open your Azure Monitor workspace
         - Go to Access Control (IAM)
         - Add role assignment → Monitoring Data Reader
         - Select the Managed Identity from step 1

      4. :ref:`Update Robusta <Simple Upgrade>` 

.. warning::

   Azure Managed Prometheus does not support the Prometheus flags API. Always set ``check_prometheus_flags: false``.

   - The prometheus URL must include port ``:443``
   - SSL is required and automatically enabled
   - AlertManager URL is not needed (Azure handles alerting separately)

Troubleshooting
---------------

**Authentication failures?**
   - Verify your Service Principal credentials or Managed Identity permissions
   - Ensure the app/identity has "Monitoring Data Reader" role on the workspace
   - Check that tenant ID and client ID are correct

**Connection errors?**
   - Verify the workspace URL includes ``:443``
   - Ensure ``PROMETHEUS_SSL_ENABLED`` is set to ``true``
   - Check that ``check_prometheus_flags`` is set to ``false``

**No metrics showing?**
   - Verify your workspace is collecting metrics from your AKS cluster
   - Check that the workspace is in the same region as your cluster (or configured for cross-region)
   - Ensure time sync between cluster and Azure

Test the connection:

.. code-block:: bash

    kubectl logs -n robusta deployment/robusta-runner | grep -i "prometheus\|azure"

Next Steps
----------

- Configure :doc:`alert routing </notification-routing/index>`
- Set up :doc:`Azure alerts integration </configuration/alertmanager-integration/azure-managed-prometheus>`
- Learn about :doc:`common configuration options <metric-providers>`