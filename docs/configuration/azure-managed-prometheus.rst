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

Configure Robusta to use Azure Managed Prometheus
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For certain features, Robusta needs to reach out to Prometheus so that Robusta can analyze and present Prometheus data.
Azure saves Prometheus metrics in an Azure Monitor Workspace. Robusta can access this data by using the Azure Monitor Workspace Query endpoint.

In order to authenticate against the Azure Monitor Workspace Query endpoint, you have multiple options:

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

- Use Azure AD Workload Identity (Option #3)

  - Pros:

    - Most secure option as Managed Identity is only bound to the pod. No other pods can use it
    - No need to manage secrets. Removing the password element decreases the risk of the credentials being compromised

  - Cons:

    - Extra setup needed: need AKS cluster with Workload Identity add-on enabled, get the OIDC issuer URL and add it to the manifests

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

   #. Open the Access Control (IAM) page for your Azure Monitor workspace in the Azure portal.
   #. Select Add role assignment.
   #. Select Monitoring Data Reader and select Next.
   #. For Assign access to, select Managed identity.
   #. Select + Select members.
   #. Select the Managed Identity you got from step 1
   #. Select Review + assign to save the configuration.

Option #3: Use Azure Workload Identity
==============================================

We will create a new Managed Identity and bound it to Robusta's Service Account so Robusta can access Prometheus data.

1. Requirements

AKS cluster needs to have Workload Identity add-on and OIDC issuer enabled. You can use `--enable-oidc-issuer --enable-workload-identity` with `az aks create` or `az aks update` to enable them.

2. Create a new Managed Identity. Change the Identity name, resource group and location to match your environment.

.. code-block:: bash

  export SUBSCRIPTION="$(az account show --query id --output tsv)"
  az identity create --name "robusta-id" --resource-group "robusta-dev" --location "eastus" --subscription "${SUBSCRIPTION}"
  az identity show --name "robusta-id" --resource-group "robusta-dev" -query clientId -o tsv # keep this value for the step #3

3. In your generated_values.yaml file add the following environment variables from the previous step.

.. code-block:: yaml

  runner:
    additional_env_vars:
    - name: PROMETHEUS_SSL_ENABLED
      value: "true"
    - name: AZURE_USE_WORKLOAD_ID
      value: "true"
    - name: AZURE_CLIENT_ID
      value: "<your-client-id>"
    - name: AZURE_TENANT_ID
      value: "<your-tenant-id>"
  azure:
    workloadIdentity:
      enabled: true

4. Federate the Service Account with the Managed Identity. Replace the values with the ones from the step #1.

.. code-block:: bash

  export AKS_OIDC_ISSUER="$(az aks show -g <resource-group> -n <cluster-name> --query "oidcIssuerProfile.issuerUrl" -otsv)" # Replace with the corresponding values of your AKS clusters.
  ROBUSTA_NAMESPACE="robusta"
  ROBUSTA_SERVICE_ACCOUNT="robusta-runner-service-account"
  az identity federated-credential create --name "robusta-federated-id" --identity-name "robusta-id" --resource-group "robusta-dev" --issuer ${AKS_OIDC_ISSUER} --subject system:serviceaccount:$ROBUSTA_NAMESPACE:$ROBUSTA_SERVICE_ACCOUNT

5. Give access to your Managed Identity on your workspace:

   #. Open the Access Control (IAM) page for your Azure Monitor workspace in the Azure portal.
   #. Select Add role assignment.
   #. Select Monitoring Data Reader and select Next.
   #. For Assign access to, select Managed identity.
   #. Select + Select members.
   #. Select the Managed Identity you got from step 2
   #. Select Review + assign to save the configuration.
