AlertManager
=============

Forward Prometheus alerts from AlertManager directly to Robusta. Robusta's per-origin parser maps AlertManager labels and annotations onto the timeline; the original payload is preserved for HolmesGPT.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts, generated under **Settings → API Keys → New API Key**.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=alertmanager&type=alert

Append ``&labels=<comma-separated-tags>`` to attach routing tags to every event from this receiver.

Configure AlertManager
----------------------

Add a webhook receiver to ``alertmanager.yml``:

.. code-block:: yaml

    receivers:
      - name: robusta
        webhook_configs:
          - url: 'https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=alertmanager&type=alert'
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

Open **Settings → Delivery Log** in the Robusta UI to see the request arrive, then check the timeline for the parsed alert.
