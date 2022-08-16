Mattermost
#################

Robusta can send playbook results to Mattermost.

To configure the Mattermost sink we will need the Mattermost bot settings

.. note::

    2-way interactivity (``CallbackBlock``) isn't implemented yet.


Get your mattermost webhook url
------------------------------------------------

1. First, go to **Main Menu > Integrations > Bot Accounts**.

    .. image:: /images/add_mattermost_bot.png
      :width: 400
      :align: center

2. If you don’t have the Integrations option in your Main Menu, bot accounts may not be enabled on your Mattermost server or may be disabled for non-admins. They can be enabled by a System Admin from System Console > Integrations > Integration Management. Then continue with the steps below.

3. Select **Add Bot Account** and add name and description for the bot. Those will be overridden by robusta when the sink is initialised, but we need to provide some values to create the bot.

    .. image:: /images/add_mattermost_bot_2.png
      :width: 600
      :align: center

    .. image:: /images/add_mattermost_bot_3.png
      :width: 600
      :align: center

    .. image:: /images/add_mattermost_bot_4.png
      :width: 600
      :align: center

4. Copy the token value of the bot - it will be used to send all the messages to the channel.

    .. image:: /images/add_mattermost_bot_5.png
      :width: 600
      :align: center

5. Copy the token id as well - it should be provided in sink variables.

    .. image:: /images/add_mattermost_bot_6.png
      :width: 600
      :align: center

6. Now we need to get the channel id we want to send the messages to. Please follow the images to find out how to get the channel id

|

    .. image:: /images/add_mattermost_bot_7.png
      :width: 400
      :align: center

|

    .. image:: /images/add_mattermost_bot_8.png
      :width: 400
      :align: center

|

    .. image:: /images/add_mattermost_bot_9.png
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
            url: <YOUR MATTERMOST URL> (can be find out from url bar in browser, e.g. namespace.cloud.mattermost.com)
            token: <YOUR BOT TOKEN> (the token we copied the first after bot creation)
            token_id: <YOUR BOT TOKEN ID> (the token id visible in bot panel)
            channel: <YOUR CHANNEL ID> (the channel id you want to send messages to)
            http_schema: <http/https> [OPTIONAL, HTTPS default] (if you want to send requests over HTTP or HTTPS)

You should now get playbooks results in Mattermost! Example is shown below:

    .. image:: /images/mattermost_sink_example.png
      :width: 1000
      :align: center
