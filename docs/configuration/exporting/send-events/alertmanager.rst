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

Replace ``<ACCOUNT_ID>`` with your Robusta account id, and ``<CLUSTER_NAME>`` with the name of the cluster to file alerts under. The name must exactly match the cluster's name as it appears in the Robusta UI (the ``clusterName`` your Robusta agent was installed with). If ``cluster`` is omitted, alerts are silently filed under a generic ``external`` cluster.

.. note::

    If you can't set the URL parameter, this endpoint also reads the cluster from a ``cluster`` or ``cluster_name`` label on each alert (for example, set via Prometheus ``externalLabels``). The ``cluster`` URL parameter takes precedence over labels. Note this is a different mechanism from the :doc:`in-cluster AlertManager integration </configuration/alertmanager-integration/outofcluster-prometheus>`, which routes by label only — following that page's label advice does not remove the need for the URL parameter (or label) here.

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
