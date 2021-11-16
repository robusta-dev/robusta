Slack Integration
#################

Robusta can send playbook results to Slack. There are two ways to set this up.

Recommended: Using Robusta's official Slack app
------------------------------------------------
When installing Robusta, run ``robusta gen-config`` and follow the prompts. This will configure Robusta to use our `official
app which was reviewed and approved by Slack <https://slack.com/apps/A0214S5PHB4-robusta?tab=more_info>`_. It works
by setting the following Helm values:

.. admonition:: values.yaml

    .. code-block:: yaml

        # slack integration params
        slackApiKey: ""
        slackChannel: ""

This method is recommended as it supports multiple Kubernetes clusters and is easy to setup. Outgoing Robusta messages
will be sent directly to Slack and incoming messages will be routed through Robusta servers to the appropriate cluster.

Not Recommended: Creating your own Slack app
-------------------------------------------------------------------
You can use Robusta with a custom Slack app as follows:

1. `Create a new Slack app. <https://api.slack.com/apps?new_app=1>`_
2. Enable Socket mode in your Slack App and copy the websocket token into the Robusta deployment yaml.
3. Under "OAuth and Permissions" add the following scopes: chat:write, files:write, incoming-webhook, and channels:history
4. Under "Event Subscriptions" add bot user events for message.channels and press "Save Changes"
5. Click "Install into Workspace"
6. Copy the signing token from basic information and the bot token from "OAuth and Permissions". Add them to the yaml

You will then need to run your own Slack relay or enable only outgoing messages. Contact us for details.