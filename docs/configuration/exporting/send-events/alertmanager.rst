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

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=alertmanager&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>

Replace ``<ACCOUNT_ID>`` with your Robusta account id and ``<CLUSTER_NAME>`` with your cluster's name exactly as it appears in the Robusta UI. If ``cluster`` is omitted, alerts are filed under a generic ``external`` cluster.

.. note::

    Alerts can also carry the cluster as a ``cluster`` or ``cluster_name`` label (e.g. via Prometheus ``externalLabels``); the URL parameter takes precedence. The :doc:`in-cluster integration </configuration/alertmanager-integration/outofcluster-prometheus>` is a separate mechanism that routes by label only.

Configure AlertManager
----------------------

Add a webhook receiver to ``alertmanager.yml``:

.. robusta-code:: yaml

    receivers:
      - name: robusta
        webhook_configs:
          - url: 'https://api.robusta.dev/webhooks?type=alert&origin=alertmanager&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>'
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
