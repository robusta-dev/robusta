Datadog
========

Forward Datadog monitor alerts to Robusta via a Datadog webhook integration.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in the Robusta UI under **Settings → General**.
* A Robusta API key with ``Read/Write`` access to alerts.
* A Datadog admin able to create webhook integrations.

Webhook URL
-----------

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=datadog&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>

Replace ``<ACCOUNT_ID>`` with your Robusta account id and ``<CLUSTER_NAME>`` with your cluster's name exactly as it appears in the Robusta UI. If ``cluster`` is omitted, Robusta uses the alert's ``kube_cluster_name`` tag, or files the alert under a generic ``external`` cluster when there is none.

Configure Datadog
-----------------

1. In Datadog, go to **Integrations → Webhooks → New** and name the webhook ``robusta``.
2. Set the URL to the webhook URL above.
3. Under **Custom Headers**, add:

   .. code-block:: json

       { "Authorization": "Bearer <ROBUSTA_API_KEY>" }

4. Replace the **Payload** with:

   .. code-block:: json

       {
         "body": "$EVENT_MSG",
         "last_updated": "$LAST_UPDATED",
         "event_type": "$EVENT_TYPE",
         "title": "$EVENT_TITLE",
         "date": "$DATE",
         "org": {"id": "$ORG_ID", "name": "$ORG_NAME"},
         "id": "$ID",
         "tags": "$TAGS",
         "aggreg_key": "$AGGREG_KEY",
         "alert_transition": "$ALERT_TRANSITION"
       }

   This is Datadog's default payload plus three fields:

   * ``tags``: cluster, namespace, and the affected Kubernetes resource (for example ``kube_deployment``, ``kube_stateful_set`` or ``pod_name``).
   * ``aggreg_key``: links a recovery to the alert it resolves.
   * ``alert_transition``: tells Robusta whether the alert is firing or recovered.

5. Save. In any monitor, set the **Notify** field to ``@webhook-robusta`` to forward its alerts to Robusta.

.. note::

    Datadog's unmodified default payload is also accepted, but alerts then carry less information and group less reliably. Use the payload above.

Verify
------

Trigger a test alert from a Datadog monitor. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.

Optional: alert names
---------------------

By default every Datadog alert is named ``Datadog alert``, so all Datadog alerts share one row on the timeline. To name alerts per monitor, add an ``alert_name`` field to the payload:

.. code-block:: json

    "alert_name": "$TAGS[alertname]"

and add a tag such as ``alertname:CrashLoopBackOff`` to each monitor. Monitors without the tag keep the default name.

.. warning::

    Use a name that is the same for every alert from a monitor. A dynamic value such as ``"$ALERT_TITLE"`` includes the pod or host that fired, so every pod or host gets its own row on the timeline.
