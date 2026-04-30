Webex
#################

Robusta can report issues and events in your Kubernetes cluster to Webex.

.. image:: /images/webex_sink/webex_sink_example.png
  :width: 1000
  :align: center

To configure the Webex sink we will need the Webex bot settings

.. note::

    2-way interactivity (``CallbackBlock``) isn't implemented yet.


Create your bot access token
------------------------------------------------

1. `Create a new bot. <https://developer.webex.com/my-apps/new/bot>`_
2. Copy and save your bot access token

.. image:: /images/webex_sink/bot_access_token.png
  :width: 600
  :align: center

3. Copy and save your bot username

.. image:: /images/webex_sink/bot_username.png
  :width: 600
  :align: center

Get your webex room ID
------------------------------------------------

1. `Click the run button here to list your room IDs. <https://developer.webex.com/docs/api/v1/rooms/list-rooms>`_ .
Copy the room ID of **the room to which you want to send Robusta notifications**.

.. image:: /images/webex_sink/room_id.png
  :width: 600
  :align: center

2. Go to `Webex spaces <https://web.webex.com/spaces>`_ **> Your space/room > People > Add People > Paste your bot username (email) > Invite > Add**.

.. note::
  The bot must be invited to the same room of which you copied the ID of in step 1.

.. image:: /images/webex_sink/add_webex_bot_to_space.png
  :width: 600
  :align: center

Configuring the webex sink
------------------------------------------------
Now we're ready to configure the webex sink.

.. admonition:: generated-values.yaml

    .. code-block:: yaml

        sinksConfig:
        - webex_sink:
            name: personal_webex_sink
            bot_access_token: <YOUR BOT ACCESS TOKEN>
            room_id: <YOUR ROOM ID>

.. note::

   To secure your bot access token using Kubernetes Secrets, see :ref:`Managing Secrets`.

You should now get playbooks results in Webex!
