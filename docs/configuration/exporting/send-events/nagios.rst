Nagios
=======

Forward Nagios host and service problems to Robusta from a Nagios notification command.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Shell access to your Nagios host with permission to edit ``commands.cfg`` and ``contacts.cfg``.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=alert&origin=nagios&account_id=<ACCOUNT_ID>

Configure Nagios
----------------

Store the API key in ``resource.cfg`` so it does not appear in command definitions or process listings:

.. code-block::

    # /etc/nagios/resource.cfg
    $USER20$=<ROBUSTA_API_KEY>

Restrict the file to the Nagios user:

.. code-block:: bash

    chown root:nagios /etc/nagios/resource.cfg
    chmod 640 /etc/nagios/resource.cfg

Define a notification command that references ``$USER20$``:

.. code-block::

    define command {
        command_name notify-robusta-service
        command_line /usr/bin/curl -sS -X POST \
            -H 'Authorization: Bearer $USER20$' \
            -H 'Content-Type: application/json' \
            --data '{
                "host": "$HOSTNAME$",
                "service": "$SERVICEDESC$",
                "state": "$SERVICESTATE$",
                "type": "$NOTIFICATIONTYPE$",
                "output": "$SERVICEOUTPUT$"
            }' \
            'https://api.robusta.dev/webhooks?type=alert&origin=nagios&account_id=<ACCOUNT_ID>'
    }

Define an analogous ``notify-robusta-host`` command, then attach both to a Nagios contact:

.. code-block::

    define contact {
        contact_name                    robusta
        service_notification_commands   notify-robusta-service
        host_notification_commands      notify-robusta-host
        service_notification_options    w,u,c,r
        host_notification_options       d,u,r
    }

Add ``robusta`` to the ``contact_groups`` you want to forward.

Verify
------

Acknowledge a test problem to fire a notification. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
