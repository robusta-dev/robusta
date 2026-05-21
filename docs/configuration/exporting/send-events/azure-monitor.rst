Azure Monitor
==============

Forward Azure Monitor alerts to Robusta via an Action Group webhook receiver.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Azure ``Contributor`` access to the resource group hosting the Action Group.

Webhook URL
-----------

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=azure&account_id=<ACCOUNT_ID>

Configure Azure
---------------

Action Group webhook receivers do not allow custom headers, so authenticate via the URL:

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=azure&account_id=<ACCOUNT_ID>&token=<ROBUSTA_API_KEY>

1. In the Azure Portal, open **Monitor → Action groups** and either create a new group or edit an existing one.
2. Under **Actions**, add an action of type **Webhook**.
3. Name it ``Robusta`` and set the **URI** to the URL above. Leave **Enable the common alert schema** on.
4. Save the action group and attach it to the alert rules you want to forward.

Verify
------

Use the action group's **Test** option. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
