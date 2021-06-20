Slack Integration
#################

There are two ways you can setup Slack integration for Robusta.

Recommended method
------------------
Using Robusta's official Slack app
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Use the `robusta install` command and when asked configure Slack via the on-screen instructions.
Done!

This method is recommended as it supports multiple Kubernetes clusters and are easy to setup.
Please note that incoming Slack messages are routed through the official Robusta
servers, however outgoing messages are sent directly to Slack. (Incoming messages need to be routed via
Robusta's servers due to `limitations of how the Slack API handles incoming messages <https://stackoverflow.com/questions/66940400/communicating-with-the-slack-api-in-multitenant-applications>`_)

Fallback method
---------------
Creating your own Slack app to use with Robusta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The above method is recommended for most users. However, if you cannot route incoming messages via
Robusta's servers, you can still use Slack with Robusta by creating your own Slack app as follows:

1. `Create a new Slack app. <https://api.slack.com/apps?new_app=1>`_
2. Enable Socket mode in your Slack App and copy the websocket token into the Robusta deployment yaml.
3. Under "OAuth and Permissions" add the following scopes: chat:write, files:write, incoming-webhook, and channels:history
4. Under "Event Subscriptions" add bot user events for message.channels and press "Save Changes"
5. Click "Install into Workspace"
6. Copy the signing token from basic information and the bot token from "OAuth and Permissions". Add them to the yaml

You will then need to run your own Slack relay or enable only outgoing messages. Contact us for details.