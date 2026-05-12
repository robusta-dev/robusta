SolarWinds
===========

Forward SolarWinds Orion alerts to Robusta from an alert action.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* SolarWinds Orion admin access.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=alert&origin=solarwinds&account_id=<ACCOUNT_ID>

Configure SolarWinds
--------------------

SolarWinds does not ship a native bearer-token webhook action. Use the **Execute an external program** action with ``curl``:

.. code-block::

    curl -sS -X POST ^
      -H "Authorization: Bearer <ROBUSTA_API_KEY>" ^
      -H "Content-Type: application/json" ^
      --data "{ \"alertName\": \"${N=Alerting;M=AlertName}\", \"node\": \"${N=SwisEntity;M=Caption}\", \"severity\": \"${N=Alerting;M=Severity}\", \"message\": \"${N=Alerting;M=AlertMessage}\" }" ^
      "https://api.robusta.dev/webhooks?type=alert&origin=solarwinds&account_id=<ACCOUNT_ID>"

Save the action and attach it to the alerts you want forwarded.

Verify
------

Manually trigger the alert from the **Alert Manager** UI. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
