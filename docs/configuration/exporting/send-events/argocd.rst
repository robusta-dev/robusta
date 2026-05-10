Argo CD
========

Forward Argo CD sync and health events to Robusta as ``change`` events.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Argo CD with the ``argocd-notifications`` controller (built into Argo CD 2.3+).

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=argocd&type=change

Configure Argo CD Notifications
--------------------------------

Add a webhook service and a template to ``argocd-notifications-cm``:

.. code-block:: yaml

    service.webhook.robusta: |
      url: https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=argocd&type=change
      headers:
        - name: Authorization
          value: Bearer <ROBUSTA_API_KEY>

    template.app-event: |
      webhook:
        robusta:
          method: POST
          body: |
            {
              "app": "{{.app.metadata.name}}",
              "namespace": "{{.app.metadata.namespace}}",
              "syncStatus": "{{.app.status.sync.status}}",
              "healthStatus": "{{.app.status.health.status}}",
              "operationState": "{{.app.status.operationState.phase}}"
            }

Subscribe applications to the trigger using the ``notifications.argoproj.io/subscribe.<trigger>.robusta`` annotation.

Verify
------

Trigger a sync on a subscribed application. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
