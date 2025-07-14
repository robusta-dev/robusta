SolarWinds Integration with Robusta
===================================

This guide explains how to configure SolarWinds to send alert webhooks directly to Robusta.

Requirements
------------

- Robusta must already be deployed and running in your environment.
- You must have access to the SolarWinds web interface with permission to manage webhooks and alert actions.

Step 1: Get Your Account ID
---------------------------

You can find your Robusta `account_id` in your `generated_values.yaml` file you used to install robusta.

Step 2: Generate an API Token
-----------------------------

1. In the Robusta UI, go to **Settings → API Keys**.
2. Click **New API Key**.
3. Name the key **SolarWinds**, grant it **Read/Write** access to alerts, and click **Generate API Key**.
4. Copy and securely store the generated API key — this will be your `ROBUSTA_API_TOKEN`.

Step 3: Create a Webhook Configuration in SolarWinds
-----------------------------------------------------

1. In the SolarWinds UI, go to **Settings → All Settings → Notification Services → Webhook**.
2. Click **Create Configuration**.
3. Fill in the form:
   - **Name**: Robusta
   - **Description**: Robusta Webhook
   - **Destination URL**:

     .. code-block::

        https://api.robusta.dev/integrations/generic/solarwinds?account_id=ACCOUNT_ID_HERE

   - Replace `ACCOUNT_ID_HERE` with your actual Robusta account ID.

4. Click **Advanced Settings** to expand the section.
5. Under **Authentication**:
   - Select **Token**.
   - **Header**: `Authorization`
   - **Value**: `Bearer ROBUSTA_API_TOKEN`

     Replace `ROBUSTA_API_TOKEN` with your real API token.

6. Click **Save**.

Step 4: Attach Webhook to Alerts
--------------------------------

You must now configure each alert you want to send to Robusta:

1. Navigate to **Alerts → Alerts Settings**.
2. For each alert you want to integrate:
   - Click **Edit**.
   - Go to the **Actions** tab.
   - Click **Add Action**.
   - Select **Webhook** as the action type.
   - For the webhook configuration, choose **Robusta**.
   - Set **Resend notification frequency** to **1 hour** (optional but recommended).
   - Toggle **Send additional notification when cleared** to **ON** (this ensures Robusta receives both firing and resolved states).
3. Save the alert.

You should now begin seeing alerts appear in the Robusta UI when they are triggered in SolarWinds.

.. note::

   The Robusta SolarWinds API integration supports the following alert types:

   - Metric Group Alerts
   - Events Alerts
   - Logs Alerts
   - Entity Alerts

   Other alert types might be supported but are not guaranteed.