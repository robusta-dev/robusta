GCP Cloud Monitoring Integration with Robusta
=============================================

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

.. note::
    Every alert must carry a ``cluster`` or ``cluster_name`` label. Set it to the Robusta ``cluster_name`` configured for the target cluster, or use ``external`` when the alerts do not belong to a specific runner.

This guide explains how to forward **GCP Cloud Monitoring alerts** to Robusta via a managed notification channel webhook.

Requirements
------------

- Robusta is deployed and running.
- You have access to the Robusta UI (to create an API key and find your ``account_id``).
- You have access to GCP Cloud Monitoring with permissions to create notification channels.

Step 1: Get Robusta Account ID and API Key
------------------------------------------

1. In the Robusta UI, go to **Settings -> API Keys**.
2. Click **New API Key**, select **Alerts: Write** permissions, and **Save**.
3. Copy the generated API key — you will use it as the password for basic authentication.
4. Find your ``account_id``:

   - In Robusta, the ``account_id`` appears in your **generated_values.yaml** file (from installation), or
   - In the Robusta UI under **Settings -> Workspace**.

Step 2: Create a Webhook Notification Channel in GCP
----------------------------------------------------

1. In the GCP Console, navigate to **Monitoring -> Alerting -> Edit Notification Channels**.
2. Under **Webhooks**, click **Add New**.
3. Configure the webhook with the following settings:

   - **Display Name**: ``RobustaWebhook``
   - **Endpoint URL**: ``https://api.robusta.dev/integrations/generic/gcp``
   - **Authentication**: Select **Basic Authentication**
   - **Username**: Your Robusta ``account_id`` from Step 1
   - **Password**: Your Robusta API key from Step 1

4. Click **Save** to create the notification channel.

Step 3: Use the Webhook in Alerting Policies
--------------------------------------------

1. Navigate to **Monitoring -> Alerting -> Policies**.
2. Create a new alerting policy or edit an existing one.
3. In the **Notifications** section, select the **RobustaWebhook** notification channel.
4. **Add a cluster label** (required): In the policy's **Documentation** section, add a custom label:

   - **Key**: ``cluster_name``
   - **Value**: Your Robusta cluster name (e.g., ``my-gcp-cluster``) or ``external`` for non-Kubernetes alerts

5. Save the alerting policy.

Validation
----------

- Trigger a test alert or wait for an existing alerting policy to fire.
- In Robusta's UI, verify the alert appears with the expected details.
