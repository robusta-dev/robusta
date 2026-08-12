Splunk
=======

Forward Splunk alerts to Robusta via a Splunk webhook alert action.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Splunk admin access to define alert actions.

Webhook URL
-----------

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=splunk&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>

Replace ``<ACCOUNT_ID>`` with your Robusta account id, and ``<CLUSTER_NAME>`` with the name of the cluster to file alerts under. The name must exactly match the cluster's name as it appears in the Robusta UI (the ``clusterName`` your Robusta agent was installed with). If ``cluster`` is omitted, alerts are silently filed under a generic ``external`` cluster.

Configure Splunk
----------------

Splunk's built-in **Webhook** alert action does not let you set custom headers, so authenticate via the URL.

1. Open or create a Splunk saved search and choose **Add Actions → Webhook**.
2. Set the **URL** to the webhook URL above with ``&token=<ROBUSTA_API_KEY>`` appended, so authentication travels with the request:

   .. robusta-code::

       https://api.robusta.dev/webhooks?type=alert&origin=splunk&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>&token=<ROBUSTA_API_KEY>

3. Save the search. If your Splunk environment has the **Webhook Alert Action** app installed, you can instead set an ``Authorization: Bearer <ROBUSTA_API_KEY>`` header and use the plain webhook URL without ``&token=…``.

Verify
------

Trigger the saved search manually. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
