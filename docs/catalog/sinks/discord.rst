Discord
#################

Robusta can send playbook results to Discord.

To configure the Discord sink we will need the Discord *webhook url*

.. note::

    2-way interactivity (``CallbackBlock``) isn't implemented yet.

Get your discord webhook url
------------------------------------------------

1. Open the Discord channel you want to receive Robusta event notifications.
2. From the channel menu, select Edit channel.

    .. image:: /images/discord_edit_channel.png
      :width: 400
      :align: center

3. Select Integrations.
4. If there are no existing webhooks, select Create Webhook. Otherwise, select View Webhooks then New Webhook.

    .. image:: /images/discord_create_webhook.png
      :width: 1000
      :align: center

5. Copy the URL from the `Copy Webhook URL` field.

    .. image:: /images/discord_copy_webhook_url.png
      :width: 1000
      :align: center

6. Select Save in the bottom.

Configuring the Discord sink
------------------------------------------------
Now we're ready to configure the Discord sink.

Edit your values.yaml (generated_values.yaml) file and add `discord_sink`. 

.. admonition:: values.yaml

    .. code-block:: yaml

        sinks_config:
        - discord_sink:
            name: personal_discord_sink
            url: <YOUR WEBHOOK URL>

Save the file and run

.. code-block:: bash
   :name: add-discord-sink

    helm upgrade robusta robusta/robusta --values=values.yaml

You should now get playbooks results in Discord! Example is shown below:

    .. image:: /images/discord_example.png
      :width: 1000
      :align: center
