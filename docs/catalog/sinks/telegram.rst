Telegram
#################

Robusta can send playbook results to Telegram conversations.

.. note::

    Tables are sent as file attachments to Telegram sinks because it's too big for most Telegram chat clients.

    In addition, 2-way interactivity (``CallbackBlock``) isn't implemented yet.

Get your Bot token
------------------------------------------------
Follow the instructions `here <https://core.telegram.org/bots#6-botfather>`_ to create a new Bot, and get your Bot token.

Chat id
------------------------------------------------
Before using the sink, you must first start the conversation with your Bot. (Locate your Bot in your Telegram app, and start the conversation)

If you want to send messages to a group, add the created Bot to your group (new or existing) and give the Bot the following group permissions: ``Send Messages``, ``Send Media``, ``Send Stickers and GIFs``

Next, we will need to obtain the ``chat id``. Checkout this `post <https://dev.to/rizkyrajitha/get-notifications-with-telegram-bot-537l#:~:text=keep%20the%20access%20token%20securely.%20Anyone%20with%20access%20token%20can%20manipulate%20your%20bot>`_ to find out how.

Configuring the Telegram sink
------------------------------------------------
Now we're ready to configure the Telegram sink.

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinks_config:
        - telegram_sink:
            name: personal_telegram sink
            bot_token: <YOUR BOT TOKEN>
            chat_id: <CHAT ID>
.. note::

    If you don't want Robusta to send file attachments, set ``send_files`` to ``False`` under your Telegram sink. (True by default)

Save the file and run

.. code-block:: bash
   :name: add-telegram-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml
    
You should now get playbooks results in Telegram!
