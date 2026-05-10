Grafana
========

Forward alerts from Grafana (Cloud or self-hosted) to Robusta via a Grafana contact point of type ``Webhook``.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Grafana 9.0+ with Grafana-managed alerting enabled.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=grafana&type=alert

Configure Grafana
-----------------

1. In Grafana, go to **Alerting → Contact points → Add contact point**.
2. Set the integration to **Webhook** and name it ``Robusta``.
3. Set the **URL** to the webhook URL above.
4. Under **Optional Webhook settings → HTTP method**, leave ``POST``. Under **Authorization Header**, set:

   * **Scheme**: ``Bearer``
   * **Credentials**: ``<ROBUSTA_API_KEY>``

5. Save the contact point.
6. Update your **Notification policy** so the desired alert rules route to ``Robusta``.

Verify
------

Use Grafana's **Test** button on the contact point. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
