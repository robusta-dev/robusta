Telegram
#################

Robusta can send playbook results to Telegram conversations.

.. note::

    ``TableBlock`` is omitted from Telegram sinks because it's too big for most Telegram chat clients.

    In addition, 2-way interactivity (``CallbackBlock``) isn't implemented yet.

Get your api_id and api_hash
------------------------------------------------
In order to run a the Telegram sink, you'll need an ``api_id`` and ``api_hash``

It's easy!

Follow the instructions `here <https://core.telegram.org/api/obtaining_api_id#obtaining-api-id>`_ to get it

Bot token
------------------------------------------------
Next we will need to get a Bot token.

Follow the instructions `here <https://core.telegram.org/bots#6-botfather>`_ to create a new Bot, and get your Bot token.

Configuring the Telegram sink
------------------------------------------------
Now we're ready to configure the Telegram sink.

We will configure the sink to send private Telegram messages in the example below.

Before using the sink, you must first start the conversation with your Bot. (Locate your Bot in your Telegram app, and start the conversation)

.. admonition:: values.yaml

    .. code-block:: yaml

        sinks_config:
        - telegram_sink:
            name: personal_telegram sink
            api_id: <YOUR API ID>
            api_hash: <YOUR API HASH>
            bot_token: <YOUR BOT TOKEN>
            recipient: <Telegram user name>

.. note::

    You can omit file attachments by setting the optional ``send_files`` to ``False`` under your Telegram sink. (True by default)

That's it.

You should now get playbooks results in Telegram!

Messaging Telegram groups
-------------------------------------------------------------------
Robusta can send playbooks results to Telegram groups as well.

The configuration is a little different.

First, add the created Bot to your group. (new or existing)

Give the Bot the following group permissions: ``Send Messages``, ``Send Media``, ``Send Stickers and GIFs``

Lastly, we will need to obtain the ``group chat id``. Checkout this `post <https://dev.to/rizkyrajitha/get-notifications-with-telegram-bot-537l#:~:text=keep%20the%20access%20token%20securely.%20Anyone%20with%20access%20token%20can%20manipulate%20your%20bot>`_ to find out how.

We can now configure the Telegram group sink:

.. admonition:: values.yaml

    .. code-block:: yaml

        sinks_config:
        - telegram_sink:
            name: group_telegram sink
            api_id: <YOUR API ID>
            api_hash: <YOUR API HASH>
            bot_token: <YOUR BOT TOKEN>
            recipient: -3243223 # your group chat id, starts with '-'
