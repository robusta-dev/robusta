LaunchDarkly Integration with Robusta
=====================================

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

This guide explains how to route LaunchDarkly feature flag changes to Robusta's UI via a webhook.

Requirements
------------

- Robusta must already be deployed and running in your environment.
- You have admin access to the Robusta UI (to create API keys and view your ``account_id``).
- You have admin access to LaunchDarkly (to create webhook integrations).

Integration Steps
-----------------

We will configure:

1. A Robusta API key and account ID.
2. A LaunchDarkly **Webhook Integration** pointing to Robusta.
3. Configure the webhook to send feature flag change events.

Step 1: Get Account ID and API Key
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Obtain your Robusta ``account_id`` and create an API key:

1. In the Robusta UI, navigate to **Settings → API Keys**.
2. Click **New API Key**.
3. Name the key **LaunchDarkly**, grant it **Read/Write** access to alerts, and click **Generate API Key**.
4. Copy and securely store the generated API key.
5. In **Settings → Workspace**, copy your **account_id**.

Step 2: Create a Webhook Integration in LaunchDarkly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In LaunchDarkly:

1. Go to **Settings → Integrations → Webhook**.
2. Click the **Add integration** button.
3. Configure:

   - **Name**: ``Robusta``
   - **URL**: ``https://api.robusta.dev/integrations/generic/launchdarkly?api_key=YOUR_API_KEY_HERE&account_id=YOUR_ACCOUNT_ID_HERE``
   - Replace ``YOUR_API_KEY_HERE`` with the API key from Step 1.
   - Replace ``YOUR_ACCOUNT_ID_HERE`` with your account ID from Step 1.

4. **Statement**: Leave as default or customize as needed.
5. **Resource type**: Select **FLAG**.
6. **Select flags**: Choose the specific flags you want to monitor, or select all.
7. **Project and environments**: Select the projects and environments you want to track.
8. Save the integration.

Alternative: Using Headers Instead of URL Parameters
--------------------------------------------------

If you're using a third-party service that can forward requests, you can alternatively configure the webhook to use headers instead of URL parameters:

- **URL**: ``https://api.robusta.dev/integrations/generic/launchdarkly``
- **Headers**:
  - ``account-id``: Your Robusta account ID
  - ``api_key``: Your Robusta API key

What Gets Tracked
-----------------

The integration automatically tracks:

- **Feature flag changes**: When flags are turned on/off, created, or modified
- **Environment changes**: Changes to flag configurations in specific environments
- **Member actions**: Who made the changes and when
- **Configuration diffs**: Before and after states of flag configurations
- **Approval workflows**: Approval requests and status changes

Alert Information
-----------------

Each LaunchDarkly change creates a Robusta alert with:

- **Title**: Descriptive title showing who made the change and what flag was affected
- **Description**: Detailed information about the change, including member details
- **Labels**: Flag key, environment, action type, and source information
- **Evidence**: 
  - Configuration diff showing before/after states
  - Markdown summary with flag details, project, environment, and reason
- **Fingerprint**: Unique identifier for change aggregation

Validation
----------

1. Make a test change to a feature flag in LaunchDarkly (turn it on/off, modify targeting, etc.).
2. In Robusta's UI, verify the alert appears with:
   - Correct flag name and environment
   - Member information (who made the change)
   - Configuration diff showing the change
   - Proper labels and annotations

Troubleshooting
---------------

- **No alerts appearing**: Verify the webhook URL is correct and the API key has proper permissions.
- **Missing member information**: Ensure the LaunchDarkly webhook payload includes member details.
- **Wrong environment**: Check that the correct projects and environments are selected in the LaunchDarkly webhook configuration.
- **Missing configuration diffs**: Ensure the webhook is configured to send both ``previousVersion`` and ``currentVersion`` data.

For additional support, check the Robusta logs for any LaunchDarkly webhook processing errors.

Holmes Configuration
-------------------

To enable Holmes to pull LaunchDarkly changes into the AI assistant, add the following configuration to your ``generated_values.yaml`` file and upgrade the Robusta Helm chart:

.. code-block:: yaml

    holmes:
      additionalEnvVars:
        - name: PULL_EXTERNAL_FINDINGS
          value: "true"

After updating the configuration:

1. Save the ``generated_values.yaml`` file.
2. Run: ``helm upgrade robusta robusta/robusta -f generated_values.yaml``
3. Restart the Holmes pod to pick up the new environment variable.

This enables Holmes to access and analyze LaunchDarkly feature flag changes, allowing you to ask questions like:
- "What feature flags were changed recently?"
- "Who modified the authentication flag?"
- "Show me all flag changes in the production environment."
