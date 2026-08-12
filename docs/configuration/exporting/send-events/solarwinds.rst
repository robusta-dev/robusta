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

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=solarwinds&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>

Replace ``<ACCOUNT_ID>`` with your Robusta account id, and ``<CLUSTER_NAME>`` with the name of the cluster to file alerts under. The name must exactly match the cluster's name as it appears in the Robusta UI (the ``clusterName`` your Robusta agent was installed with). If ``cluster`` is omitted, alerts are silently filed under a generic ``external`` cluster.

Configure SolarWinds
--------------------

SolarWinds does not ship a native bearer-token webhook action. Use the **Execute an external program** alert action to invoke ``curl`` (bundled with Windows 10+ and Windows Server 2019+):

.. robusta-code::

    curl -sS -X POST -H "Authorization: Bearer <ROBUSTA_API_KEY>" -H "Content-Type: application/json" --data "{ \"alertName\": \"${N=Alerting;M=AlertName}\", \"node\": \"${N=SwisEntity;M=Caption}\", \"severity\": \"${N=Alerting;M=Severity}\", \"message\": \"${N=Alerting;M=AlertMessage}\" }" "https://api.robusta.dev/webhooks?type=alert&origin=solarwinds&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>"

Save the action and attach it to the alerts you want forwarded.

Verify
------

Manually trigger the alert from the **Alert Manager** UI. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
