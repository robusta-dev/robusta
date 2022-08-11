Mattermost
#################

Robusta can send playbook results to Mattermost.

To configure the Mattermost sink we will need the Mattermost webhook url

.. note::

    2-way interactivity (``CallbackBlock``) isn't implemented yet.

    Files attachments are not supported by Mattermost webhook yet.

Get your mattermost webhook url
------------------------------------------------

1. First, go to **Main Menu > Integrations > Incoming Webhook**.

    .. image:: /images/add_mattermost_sink.png
      :width: 400
      :align: center

2. If you don’t have the Integrations option in your Main Menu, incoming webhooks may not be enabled on your Mattermost server or may be disabled for non-admins. They can be enabled by a System Admin from System Console > Integrations > Integration Management. Then continue with the steps below.

3. Select **Add Incoming Webhook** and add name and description for the webhook. The description can be up to 500 characters.

    .. image:: /images/add_mattermost_sink_2.png
      :width: 400
      :align: center

4. Select the channel to receive webhook payloads, then click Add to create the webhook.

.. note::

    **Enable integrations to override usernames** and **Enable integrations to override profile picture icons**
    must be set to true. Enable them from System Console > Integrations > Integration Management,
    or ask your System Admin to do so. If not enabled, the icon of the creator of the webhook URL is used to post messages.


Enabling override usernames and profile picture
***************************************

1. First, go to **Main Menu > Integrations > System Console**. (It may not be enabled on your Mattermost server or may be disabled for non-admins.)

    .. image:: /images/admin_console_mattermost.png
      :width: 400
      :align: center

2. Select **Integration Management** from menu on the left.

3. Check both **Enable integrations to override usernames** and **Enable integrations to override profile picture icons**
    to true.

    .. image:: /images/admin_console_mattermost_2.png
      :width: 400
      :align: center

Configuring the Mattermost sink
------------------------------------------------
Now we're ready to configure the Mattermost sink.

.. admonition:: values.yaml

    .. code-block:: yaml

        sinks_config:
        - mattermost_sink:
            name: personal_mattermost_sink
            url: <YOUR WEBHOOK URL>
            channel: <YOUR WEBHOOK CHANNEL> [OPTIONAL]

You should now get playbooks results in Mattermost! Example is shown below:

    .. image:: /images/mattermost_sink_example.png
      :width: 1000
      :align: center
