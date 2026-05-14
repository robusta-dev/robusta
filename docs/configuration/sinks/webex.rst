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

You should now get playbooks results in Webex!

Dynamic Room Routing
------------------------------------------------

You can route alerts to different Webex rooms based on Kubernetes labels or
annotations. The sink supports two override fields, evaluated in order:

1. ``namespace_room_id_override`` — resolved against the **Namespace** object's labels
   and annotations (looked up by the finding's namespace, with TTL caching to avoid
   hammering the K8s API).
2. ``room_id_override`` — resolved against the finding's **subject** labels and
   annotations (same behavior as Slack's ``channel_override``).

If neither override produces a room id, ``send_to_default_if_missing`` decides what
happens:

- ``true`` *(default)* — send to the configured ``room_id``.
- ``false`` — drop the finding silently.

Both override fields use the same template syntax as Slack:

- ``cluster_name`` — the Robusta cluster name.
- ``labels.foo`` / ``$labels.foo`` — value of a label.
- ``annotations.bar`` / ``$annotations.bar`` — value of an annotation.
- ``${labels.foo-bar}`` / ``${annotations.kubernetes.io/owner}`` — bracket form
  required when the key contains characters other than letters, digits, or underscores
  (e.g. ``-``, ``/``, ``.``).
- Composite patterns are allowed: ``"$cluster_name-$labels.team"``.

Example — route by a label on the namespace, fall back to the default room:

.. code-block:: yaml

    sinksConfig:
    - webex_sink:
        name: webex_sink
        bot_access_token: <YOUR BOT ACCESS TOKEN>
        room_id: <DEFAULT ROOM ID>
        namespace_room_id_override: "${labels.webex-room}"
        send_to_default_if_missing: true

Example — route by namespace label first, fall back to a subject label, drop if neither
is present:

.. code-block:: yaml

    sinksConfig:
    - webex_sink:
        name: webex_sink
        bot_access_token: <YOUR BOT ACCESS TOKEN>
        room_id: <DEFAULT ROOM ID>
        namespace_room_id_override: "${labels.webex-room}"
        room_id_override: "$labels.team"
        send_to_default_if_missing: false
