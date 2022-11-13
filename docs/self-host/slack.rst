Create a Slack application
#############################

You need a custom Slack application for your organization so your self hosted Robusta can send alerts to Slack.

Prerequisites
------------------------------

* Have a self_host_values.yaml configuration file.

Set up the app template json
---------------------------------

We’ll use a template to create a Robusta app.

* Copy the template to a file and replace all instances of **MY_DOMAIN** in the template with your domain.

You can also find MY_DOMAIN in your self_host_values.yaml file under DOMAIN.

.. code-block:: json
   :name: cb-slack-app-json

    {
        "display_information": {
            "name": "Robusta (self-hosted)",
            "description": "Robusta automates Kubernetes maintenance directly from your Slack workspace",
            "background_color": "#565659",
            "long_description": "Improving cloud maintenance by providing state-of-the art automation tools.\r\n\r\nTurn your operations into re-usable runbooks that were built for the modern cloud. \r\n\r\nShare best practices with your colleagues for automatically enriching errors, troubleshooting bugs, and remediating known issues."
        },
        "features": {
            "bot_user": {
                "display_name": "Robusta (self-hosted)",
                "always_online": false
            }
        },
        "oauth_config": {
            "redirect_urls": [
                "https://api.MY_DOMAIN/integrations/slack/code-verify"
            ],
            "scopes": {
                "bot": [
                    "chat:write",
                    "chat:write.public",
                    "files:write"
                ]
            }
        },
        "settings": {
            "interactivity": {
                "is_enabled": true,
                "request_url": "https://api.MY_DOMAIN/integrations/slack/handle-action"
            },
            "org_deploy_enabled": false,
            "socket_mode_enabled": false,
            "token_rotation_enabled": false
        }
    }
   
Build and Install the Slack app
--------------------------------

#. Go to `Slack apps <https://api.slack.com/apps/>`_ 
#. Click create new app (on top right corner).
#. Choose “From app manifest”  (down on the left menu).
#. Choose your desired workspace. (step 1)
#. Choose JSON format (step 2), and paste your copy of the app template into the form.
#. Select create (step 3)
#. Go to your app page -> Basic Information
#. Find ``Install your app`` and install it to the relevant workspace.
#. Go to ``Display Information`` and add our :download:`App icon </_static/app-logo.png>`

Use the created app credentials
--------------------------------------

In this part we will update the self_host_values.yaml file to use your app credentials.

#. Go to your app page -> Basic Information
#. In the App Credentials section find: ``Client ID``, ``Client Secret`` and ``Signing Secret``.
#. Open the self_host_values.yaml file
#. replace ``slackClientId``, ``slackClientSecret`` and ``slackSigningSecret`` respectively.