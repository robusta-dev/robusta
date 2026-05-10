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

    https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=nagios&type=alert

Configure Nagios
----------------

Nagios delivers notifications by running shell commands. Define a command that POSTs the alert as JSON.

Store the API key in ``resource.cfg`` rather than inlining it in ``commands.cfg`` so that it does not appear in command definitions, command-line process listings, or backups of the main configuration:

.. code-block::

    # /etc/nagios/resource.cfg
    $USER20$=<ROBUSTA_API_KEY>

Nagios resource macros are intentionally not exposed to the CGIs and can hold secrets. Tighten the file permissions so only the Nagios user can read it, and exclude ``resource.cfg`` from any unprotected backup or config-management bundle:

.. code-block:: bash

    chown root:nagios /etc/nagios/resource.cfg
    chmod 640 /etc/nagios/resource.cfg

Then reference ``$USER20$`` from the notification command:

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
            'https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=nagios&type=alert'
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
