New Relic
==========

Forward New Relic alerts to Robusta via a New Relic webhook destination.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* A New Relic admin able to create webhook destinations.

Webhook URL
-----------

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=newrelic&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>

Replace ``<ACCOUNT_ID>`` with your Robusta account id, and ``<CLUSTER_NAME>`` with the name of the cluster to file alerts under. The name must exactly match the cluster's name as it appears in the Robusta UI (the ``clusterName`` your Robusta agent was installed with). If ``cluster`` is omitted, alerts are silently filed under a generic ``external`` cluster.

Configure New Relic
-------------------

1. In New Relic, go to **Alerts & AI → Destinations** and add a **Webhook** destination named ``Robusta``.
2. Set the **Endpoint URL** to the webhook URL above.
3. Add a custom header:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

4. Use the default payload template.
5. Create a **Workflow** that routes the desired policy to this destination.

Verify
------

Trigger a test incident in New Relic. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
