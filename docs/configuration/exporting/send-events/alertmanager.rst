AlertManager
=============

Forward Prometheus alerts from AlertManager directly to Robusta.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts, generated under **Settings → API Keys → New API Key**.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=alert&origin=alertmanager&account_id=<ACCOUNT_ID>

Configure AlertManager
----------------------

Add a webhook receiver to ``alertmanager.yml``:

.. code-block:: yaml

    receivers:
      - name: robusta
        webhook_configs:
          - url: 'https://api.robusta.dev/webhooks?type=alert&origin=alertmanager&account_id=<ACCOUNT_ID>'
            send_resolved: true
            http_config:
              authorization:
                type: Bearer
                credentials: <ROBUSTA_API_KEY>

    route:
      receiver: robusta
      continue: true

Set ``continue: true`` if Robusta is not your only receiver, so alerts also reach your other destinations.

Verify
------

The alert should appear on the Robusta timeline.
