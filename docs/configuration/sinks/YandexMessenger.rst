Yandex Messenger
#################

Robusta can report issues and events in your Kubernetes cluster to Yandex Messenger chats, channels or private conversations.

.. note::

    Tables (alert labels, events etc.) are sent as file attachments because they are not rendered properly in Yandex Messenger clients.

    2-way interactivity (``CallbackBlock``) is not implemented in this sink.

Obtaining your Bot token
------------------------------------------------
Follow the quickstart guide in the Yandex Messenger `docs <https://botapi.messenger.yandex.net/docs/#quickstart-guide>`_ to create a new Yandex Messenger bot, and obtain its OAuth token.

Adding your Bot to your chat/channel and obtaining the chat ID
------------------------------------------------------------------
Before using the sink, you must add your Bot to the target chat or channel as an administrator.

You also need to get the chat ID. It has the following format ``<integer>/<integer>/<uuid>`` and can be obtained by opening the chat or channel in the web version of Yandex Messenger and url-decoding the last fragment of the page URL path.

Configuring the Yandex Messenger sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - yamessenger_sink:
            name: my_yamessenger_sink
            bot_token: <YOUR BOT TOKEN>
            chat_id: <YOUR CHAT ID>
            user_name: # Send messages to a private conversation with a user (user@domain), mutually exclusive with chat_id, optional
            disable_notifications: # Disable notifications for sent messages, default = false
            disable_links_preview: # Disable links preview, dafault = true
            mark_important: # Mark sent messages as important, default = false
            send_files: # Send files (logs, images), default = true

File attachments
------------------------------------------------
This sink sends file attachments (text files and images) by default.
Here are some examples of how that might look in your chat or channel:

.. image:: /images/yamessenger_sink/yamessenger-file-attachment.png
  :width: 600
  :align: center

.. image:: /images/yamessenger_sink/yamessenger-image-attachment.png
  :width: 600
  :align: center

If you don't want Robusta to send file attachments, set ``send_files`` to ``False`` in your Yandex Messenger sink configuration.

After you have configured the sink in your ``generated_values.yaml`` save the file and run:

.. code-block:: bash
   :name: cb-add-yamessenger-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

.. note::

   To secure your bot token using Kubernetes Secrets, see :ref:`Managing Secrets`.

You should now get playbooks results in Yandex Messenger!
