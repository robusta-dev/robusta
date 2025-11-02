Dynatrace Integration with Robusta
==================================

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

This guide explains how to forward **Dynatrace problem notifications** to Robusta via a webhook.

Requirements
------------

- Robusta is deployed and running.
- You have access to the Robusta UI (to create an API key and find your ``account_id``).
- You have admin access to the Dynatrace platform (to configure Problem notifications).

Step 1: Get Robusta Account ID and API Key
------------------------------------------

1. In the Robusta UI, go to **Settings → API Keys**.
2. Click **New API Key**, select **Alerts: Write** permissions, and **Save**.
3. Copy the generated API key — you will use it as a Bearer token in Dynatrace.
4. Find your ``account_id``:
   - In Robusta, the ``account_id`` appears in your **generated_values.yaml** file (from installation), or
   - In the Robusta UI under **Settings → Workspace**.

Step 2: Create a Dynatrace Problems Webhook
-------------------------------------------

1. In Dynatrace, open the **command palette** (**Cmd+K** on macOS / **Ctrl+K** on Windows/Linux).
2. Search for **problem notification** and open **Problem notifications**.
3. Click **Add notification** and choose **Webhook**.
4. Configure the **URL**:

   ``https://api.robusta.dev/integrations/generic/dynatrace``

5. Set the **Custom payload** to the Dynatrace macro:

   .. code-block:: text

      {ProblemDetailsJSONv2}

6. Add the following **HTTP headers**:

   .. code-block:: text

      Authorization: Bearer <api-key>
      account-id: <account_id>

   Replace ``<api-key>`` with the Robusta API key from Step 1 and ``<account_id>`` with your Robusta account ID.

7. Save the webhook notification.

