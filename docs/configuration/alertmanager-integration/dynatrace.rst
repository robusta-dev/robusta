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

   .. code-block:: json

      {ProblemDetailsJSONv2}

6. Add the following **HTTP headers**:

   .. code-block:: http

      Authorization: Bearer <api-key>
      account-id: <account_id>

   Replace ``<api-key>`` with the Robusta API key from Step 1 and ``<account_id>`` with your Robusta account ID.

7. Save the webhook notification.

Validation
----------

- In Dynatrace, use **Send test notification** (if available) on the webhook to verify connectivity.
- Alternatively, trigger a test problem that matches your environment.
- In Robusta’s UI, confirm the alert appears with the expected title, description, and problem details.

What the Payload Contains
-------------------------

- ``{ProblemDetailsJSONv2}`` expands to Dynatrace’s full problem JSON (v2), including problem ID, status/open/closed times, impacted entities, evidence, and root cause information.
- Robusta stores the original Dynatrace payload for troubleshooting and enrichment.

Troubleshooting
---------------

- **401/403 Unauthorized**: Ensure the **Authorization** header uses a valid Robusta API key with **Alerts: Write** permissions.
- **Missing or incorrect account**: Confirm the **account-id** header exactly matches your Robusta ``account_id`` from **generated_values.yaml** (or **Settings → Workspace**).
- **Not receiving alerts**: Verify the Dynatrace webhook is **enabled**, the URL is exactly
  ``https://api.robusta.dev/integrations/generic/dynatrace``, and that problems are actually being generated in your environment.
- **Firewall/egress**: Ensure the Dynatrace environment can reach ``api.robusta.dev`` over HTTPS (TCP 443).

Change Management
-----------------

- If you rotate the Robusta API key, update the **Authorization** header in Dynatrace accordingly.
- If you migrate workspaces or tenants and your ``account_id`` changes, update the **account-id** header.
