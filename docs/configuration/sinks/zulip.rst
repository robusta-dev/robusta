Zulip
######

Robusta can report issues and events in your Kubernetes cluster to Zulip.

.. image:: /images/zulip_example.png
    :width: 1000
    :align: center

To configure the Zulip sink you will need a *bot email*, an *api token* and the api url

Creating a bot account
-----------------------

1. Open Zulip
2. Click on the gear icon in the upper right corner
3. Select **Personal** or **Organization** settings
4. On the left, click **Bots**
5. Click **Add a new bot**
6. Fill out the fields, and click **Add**
4. Copy email and token

Settings
------------------

* ``api_url`` : The url of your Zulip instance
* ``bot_email`` : The email of the bot account
* ``bot_api_key`` : The api key of your bot account
* ``stream_name`` : Name of the channel to send the message to
* ``topic_name`` : Name of the topic of the stream to send messages to
* ``topic_override`` : Dynamic topic override, same as the channel_override in the slack sink
* ``log_preview_char_limit`` : [Optional - default: ``500``] The amount of log lines to append to the alert message (zulip doesnt have a builtin text file preview). If set to ``0`` a text file will be sent

Configuring the Zulip sink
---------------------------

.. admonition:: Add this to your generated_values.yaml

   .. code-block:: yaml

        sinksConfig:
        - zulip_sink:
            name: my_zulip_sink
            api_url: https://my-zulip-instance.com
            bot_email: bot12345@my-zulip-instance.com
            bot_api_key: very_secret_key
            stream_name: Monitoring
            topic_name: Robusta

Save the file and run

.. code-block:: bash
   :name: cb-add-zulip-sink

   helm upgrade robusta robusta/robusta -f generated_values.yaml

You should now get alerts in Zulip!
