New Relic Integration with Robusta
==================================

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

This guide explains how to route New Relic alerts to Robusta's UI via a webhook.

Requirements
------------

- Robusta must already be deployed and running in your environment.
- You have admin access to the Robusta UI (to create API keys and view your ``account_id``).
- You have admin access to New Relic Alerts (to create Destinations and Workflows).

Integration Steps
-----------------

We will configure:

1. A Robusta API key and account ID.
2. A New Relic **Webhook Destination** pointing to Robusta.
3. A New Relic **Workflow** that always sends notifications to Robusta using a custom payload template.

Step 1: Get Account ID and API Key
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Obtain your Robusta ``account_id`` and create an API key:

1. In the Robusta UI, navigate to **Settings → API Keys**.
2. Click **New API Key**.
3. Name the key **New Relic**, grant it **Read/Write** access to alerts, and click **Generate API Key**.
4. Copy and securely store the generated API key — you’ll use it as a **Bearer token** in New Relic.
5. In **Settings → Workspace**, copy your **account_id**.

Step 2: Create a Webhook Destination in New Relic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In New Relic:

1. Go to **Alerts → Destinations**.
2. Click **New destination** → choose **Webhook**.
3. Configure:

   - **URL**: ``https://api.robusta.dev/integrations/generic/newrelic``
   - **Authentication**: **Bearer token**
   - **Token**: paste the **Robusta API key** from Step 1.

4. Save the destination. (Optional) Use **Send test notification** to verify connectivity.

Step 3: Configure a Workflow to Send Alerts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Go to **Alerts → Workflows**.
2. Use an existing workflow or click **New workflow**.
3. **When**: set to **Always send notifications** (or choose your preferred filter).
4. **Then**: add an **Action → Webhook** and select the **Robusta** destination created in Step 2.
5. **Template**: choose **Custom payload** and paste the JSON template below.
6. Replace ``ACCOUNT_ID_HERE`` with your **account_id** from Step 1.
7. Save and enable the workflow.

Webhook Payload Template (JSON)
-------------------------------

Paste this into the **Template** field for the webhook action. Replace ``ACCOUNT_ID_HERE`` with your actual account ID.

.. code-block:: json

    {
      "account_id": "ACCOUNT_ID_HERE",
      "title": {{#if annotations}}{{#if annotations.title}}{{ json annotations.title.[0] }}{{else}}"N/A"{{/if}}{{else}}"N/A"{{/if}},
      "description": {{#if annotations}}{{#if annotations.description}}{{ json annotations.description.[0] }}{{else}}{{#if annotations.title}}{{ json annotations.title.[0] }}{{else}}"N/A"{{/if}}{{/if}}{{else}}"N/A"{{/if}},
      "source": "newrelic",
      "priority": {{#if priority}}{{ json priority }}{{else if severity}}{{ json severity }}{{else}}null{{/if}},
      "aggregation_key": {{#if accumulations.conditionName}}{{ json accumulations.conditionName.[0] }}{{else}}null{{/if}},
      "starts_at": {{#if createdAt}}{{#timezone createdAt 'UTC'}}{{/timezone}}{{else}}"2025-09-22 00:00:00 UTC"{{/if}},
      "ends_at": {{#eq state "CLOSED"}}{{#if updatedAt}}{{#timezone updatedAt 'UTC'}}{{/timezone}}{{else}}null{{/if}}{{else}}null{{/eq}},
      "cluster": {{#if [latest clusterName]}}
        {{ json [latest clusterName] }}
      {{else if accumulations}}
        {{#if accumulations.tag}}
          {{#if accumulations.tag.k8s.clusterName}}
            {{ json accumulations.tag.k8s.clusterName.[0] }}
          {{else if accumulations.tag.cluster}}
            {{ json accumulations.tag.cluster.[0] }}
          {{else if tag.k8s.clusterName}}
            {{ json tag.k8s.clusterName.[0] }}
          {{else}}
            "external"
          {{/if}}
        {{else}}
          "external"
        {{/if}}
      {{else}}
        "external"
      {{/if}},
      "raw_alert_data": {{ json . }}
    }

Optional: Field Mapping Notes
-----------------------------

- ``title`` / ``description`` are sourced from ``annotations`` when present, otherwise fall back to ``"N/A"``.
- ``priority`` prefers ``priority`` and falls back to ``severity`` when available.
- ``aggregation_key`` maps to the Alert name to help group similar alerts in Robusta.
- ``starts_at`` / ``ends_at`` are normalized to **UTC** by New Relic templating.
- ``cluster`` attempts multiple common locations for Kubernetes cluster identifiers and defaults to ``"external"``.
- ``raw_alert_data`` includes the full New Relic payload for troubleshooting in Robusta.

Validation
----------

- Trigger a test alert that matches the workflow (or use **Send test notification** on the Destination).
- In Robusta's UI, verify the alert appears with the expected title, description, priority, and cluster.
