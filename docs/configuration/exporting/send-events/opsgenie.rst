Opsgenie
=========

Forward Opsgenie alerts to Robusta via the Opsgenie outgoing webhook integration.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Opsgenie admin access.

Webhook URL
-----------

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=opsgenie&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>

Replace ``<ACCOUNT_ID>`` with your Robusta account id, and ``<CLUSTER_NAME>`` with the name of the cluster to file alerts under. The name must exactly match the cluster's name as it appears in the Robusta UI (the ``clusterName`` your Robusta agent was installed with). If ``cluster`` is omitted, alerts are silently filed under a generic ``external`` cluster.

Configure Opsgenie
------------------

1. In Opsgenie, go to **Settings → Integrations → Add Integration → Webhook**.
2. Set the **Webhook URL** to the URL above.
3. Add a custom **Header**:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

4. Choose which alert actions (``Create``, ``Acknowledge``, ``Close``, …) trigger the webhook and save.

Verify
------

Create a test alert in Opsgenie. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
