Slack
#################

Robusta can send playbook results to Slack. There are two ways to set this up.

Recommended: Using Robusta's official Slack app
------------------------------------------------
When installing Robusta, run ``robusta gen-config`` and follow the prompts. This will use our `official
Slack app <https://slack.com/apps/A0214S5PHB4-robusta?tab=more_info>`_.

**Robusta can only write messages. We don't require read permissions.**

You can also generate a key by running ``robusta integrations slack`` and setting the following Helm values:

.. admonition:: values.yaml

    .. code-block:: yaml

        sinks_config:
        # slack integration params
        - slack_sink:
            name: main_slack_sink
            api_key: MY SLACK KEY
            slack_channel: MY SLACK CHANNEL


This method is recommended as it supports multiple Kubernetes clusters and is easy to setup. Outgoing messages
are sent directly to Slack. Incoming messages are routed through Robusta servers to the appropriate cluster.

Not Recommended: Creating your own Slack app
-------------------------------------------------------------------
You can use Robusta with a custom Slack app as follows:

1. `Create a new Slack app. <https://api.slack.com/apps?new_app=1>`_
2. Enable Socket mode in your Slack App and copy the websocket token into the Robusta deployment yaml.
3. Under "OAuth and Permissions" add the following scopes: chat:write, files:write, incoming-webhook, and channels:history
4. Under "Event Subscriptions" add bot user events for message.channels and press "Save Changes"
5. Click "Install into Workspace"
6. Copy the signing token from basic information and the bot token from "OAuth and Permissions". Add them to the yaml

You will then need to run your own Slack relay or enable only outgoing messages. :ref:`Contact us for details. <Getting Support>`