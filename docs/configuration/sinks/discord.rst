Discord
#################

Robusta can report issues and events in your Kubernetes cluster to Discord.

.. image:: /images/discord_example.png
    :width: 1000
    :align: center

To configure the Discord sink we will need the Discord *webhook url*

.. note::

    2-way interactivity (``CallbackBlock``) isn't implemented yet.

Getting your discord webhook url
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

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - discord_sink:
            name: personal_discord_sink
            url: <YOUR WEBHOOK URL>

Save the file and run

.. code-block:: bash
   :name: cb-add-discord-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

.. note::

   To secure your webhook URL using Kubernetes Secrets, see :ref:`Managing Secrets`.

You should now get playbooks results in Discord!


Discord configuration tutorial
---------------------------------

See video below:

.. raw:: html

    <div style="position: relative; padding-bottom: 62.5%; height: 0;"><iframe src="https://www.loom.com/embed/f74a448135ed4da28120c5e21def1df9" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>
