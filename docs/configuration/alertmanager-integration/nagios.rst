Nagios Integration with Robusta
===============================

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

This guide explains how to set up Nagios to send alert webhooks to Robusta.

Requirements
------------

- Robusta must already be deployed and running in your environment.
- The Nagios host must be able to send `curl` requests to the Robusta API endpoint:

  .. code-block::

     https://api.robusta.dev/integrations/generic/nagios


Integration Steps
-----------------

We will configure:

1. A Nagios contact for Robusta.
2. A Bash script to send alerts.
3. Two Nagios commands (for host and service alerts).

Step 1: Get Account ID and Token
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Obtain your Robusta `account_id` from your `generated_values.yaml`.

To generate an API token:

1. In the Robusta UI, navigate to **Settings → API Keys**.
2. Click **New API Key**.
3. Name the key **Nagios**, grant it **Read/Write** access to alerts, and click **Generate API Key**.
4. Copy and securely store the generated API key — you’ll use this as your `api_token`.


Step 2: Define the Robusta Contact
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Insert the following contact definition into your Nagios configuration to register Robusta as a notification target. Be sure to replace the placeholders for `_account_id` and `_robusta_api_token` with your actual values.

.. code-block:: text

    define contact {
        contact_name                    robusta
        alias                           Robusta Webhook
        service_notification_period     24x7
        host_notification_period        24x7
        service_notification_options    w,u,c,r
        host_notification_options       d,u,r
        service_notification_commands   notify-service-by-robusta
        host_notification_commands      notify-host-by-robusta
        _account_id                     ******
        _robusta_api_token              ******
    }


Step 3: Add Robusta to a Contact Group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure Robusta is part of a contact group or explicitly included in your alert definitions:

.. code-block:: text

    define contactgroup {
        contactgroup_name               all_contacts
        alias                           Nagios Administrators
        members                         (other contacts listed here),robusta
    }

Step 4: Create the Bash Command Script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Save this as `notify-robusta.sh`, ensure it's executable (`chmod +x notify-robusta.sh`), and Nagios can access it.

.. code-block:: bash

    #!/bin/sh

    # Usage:
    #   ./notify-robusta.sh -n host|service -t NOTIFICATIONTYPE \
    #       -f key=value -f key=value ... -f account_id=... -f api_token=...

    alert_type=""
    notification_type=""
    account_id=""
    api_token=""
    json=""

    while [ "$#" -gt 0 ]; do
      case "$1" in
        -n)
          alert_type="$2"
          shift 2
          ;;
        -t)
          notification_type="$2"
          shift 2
          ;;
        -f)
          kv="$2"
          key=$(printf "%s" "$kv" | cut -d'=' -f1)
          value=$(printf "%s" "$kv" | cut -d'=' -f2-)

          if [ "$key" = "account_id" ]; then
            account_id="$value"
          elif [ "$key" = "api_token" ]; then
            api_token="$value"
          else
            esc_key=$(printf "%s" "$key" | sed 's/\\/\\\\/g; s/"/\\"/g')
            esc_val=$(printf "%s" "$value" | sed 's/\\/\\\\/g; s/"/\\"/g')
            [ -n "$json" ] && json="$json,"
            json="$json\"$esc_key\":\"$esc_val\""
          fi
          shift 2
          ;;
        *)
          echo "Unknown argument: $1"
          exit 1
          ;;
      esac
    done

    [ -z "$account_id" ] || [ -z "$api_token" ] && {
      echo "Missing account_id or api_token"
      exit 2
    }

    json="{$json}"

    curl -X POST "https://api.robusta.dev/integrations/generic/nagios" \
         -H "Content-Type: application/json" \
         -H "account-id: $account_id" \
         -H "Authorization: Bearer $api_token" \
         -d "$json"

Step 5: Define Robusta Notification Commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before proceeding, if your Nagios setup monitors multiple clusters, you can optionally set the `cluster_name` variable per host using custom `_cluster_name` properties:

.. code-block:: text

    define host {
        host_name       order-management
        alias           checkout.robusta-payments.com
        address         10.100.253.97
        ...
        _cluster_name   eu-prod-atc-eks
    }

    define host {
        host_name       payment-processor
        alias           api.robusta-payments.com
        address         10.100.183.73
        ...
        _cluster_name   eu-stg-eks
    }

Now, define the notification commands and replace `PATH_TO_SCRIPT_HERE` with the actual path to your Bash script (`notify-robusta.sh`).

.. code-block:: text

    define command {
        command_name    notify-service-by-robusta
        command_line    PATH_TO_SCRIPT_HERE/notify-robusta.sh \
            -f account_id="$_CONTACTACCOUNT_ID$" \
            -f api_token="$_CONTACTROBUSTA_API_TOKEN$" \
            -f fingerprint="$SERVICEPROBLEMID$" \
            -f notification_type="$NOTIFICATIONTYPE$" \
            -f host="$HOSTNAME$" \
            -f host_display_name="$HOSTDISPLAYNAME$" \
            -f service="$SERVICEDESC$" \
            -f service_display_name="$SERVICEDISPLAYNAME$" \
            -f service_state="$SERVICESTATE$" \
            -f service_output="$SERVICEOUTPUT$" \
            -f service_check_command="$SERVICECHECKCOMMAND$" \
            -f long_datetime="$LONGDATETIME$" \
            -f cluster_name="$_HOSTCLUSTER_NAME$"
    }

    define command {
        command_name    notify-host-by-robusta
        command_line    PATH_TO_SCRIPT_HERE/notify-robusta.sh \
            -f account_id="$_CONTACTACCOUNT_ID$" \
            -f api_token="$_CONTACTROBUSTA_API_TOKEN$" \
            -f fingerprint="$HOSTPROBLEMID$" \
            -f notification_type="$NOTIFICATIONTYPE$" \
            -f host="$HOSTNAME$" \
            -f host_display_name="$HOSTDISPLAYNAME$" \
            -f host_state="$HOSTSTATE$" \
            -f host_output="$HOSTOUTPUT$" \
            -f host_check_command="$HOSTCHECKCOMMAND$" \
            -f long_datetime="$LONGDATETIME$" \
            -f cluster_name="$_HOSTCLUSTER_NAME$"
    }

Step 6: Add Extra Variables (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To include additional data in alerts, use:

.. code-block:: bash

    -f variable_name="$INTERNAL_VARIABLE_NAME$"

Example:

.. code-block:: bash

    -f contact_email="$_CONTACTEMAIL$"

Restart Nagios to apply your changes:

.. code-block:: bash

    systemctl restart nagios
