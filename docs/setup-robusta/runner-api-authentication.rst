Runner API Authentication
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The robusta-runner HTTP API (for example ``/api/alerts``) only accepts requests
that carry the runner's token as a bearer token:

.. code-block:: text

    Authorization: Bearer <account_id> <signing_key>

The token defaults to ``globalConfig.account_id`` and ``globalConfig.signing_key``,
separated by a space. The bundled ``kube-prometheus-stack`` AlertManager sends it
automatically. ``/healthz``, ``/metrics`` and the endpoints used by the Robusta
forwarder and KRR scan jobs do not require it.

Rejected Requests
-------------------------------------

A request without the token is answered with ``401`` and logged by the runner:

.. code-block:: text

    Rejected unauthenticated request to /api/alerts from 10.0.0.12. If this request was intended, see https://docs.robusta.dev/master/setup-robusta/runner-api-authentication.html to set its token or disable authentication.

If the request was intended, either send the token from that service or disable authentication.

Sending the Token
-------------------------------------

For an external AlertManager, add the token to the Robusta receiver:

.. code-block:: yaml

    receivers:
      - name: 'robusta'
        webhook_configs:
          - url: 'http://<helm-release-name>-runner.<namespace>.svc.cluster.local/api/alerts'
            send_resolved: true
            http_config:
              authorization:
                credentials: '<account_id> <signing_key>'

Any other client sends the same value in the ``Authorization`` header.

Setting a Custom Token
-------------------------------------

Set ``runner.apiAuth.token`` in your Helm values to use a different token. This is
required when ``account_id`` or ``signing_key`` are
:ref:`loaded from an environment variable <Managing Secrets>`, as Helm cannot read their values:

.. code-block:: yaml

    runner:
      apiAuth:
        token: "<your token>"

The token is stored in the ``robusta-runner-api-token`` Secret. If you override
``kube-prometheus-stack.alertmanager.alertmanagerSpec.secrets`` or the ``robusta``
receiver, keep that Secret and the receiver's ``http_config``.

Disabling Authentication
-------------------------------------

.. code-block:: yaml

    runner:
      apiAuth:
        enabled: false

When no token is set and ``account_id`` and ``signing_key`` are both empty,
authentication is disabled as well.
