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

    https://api.robusta.dev/webhooks?type=change&origin=argocd&account_id=<ACCOUNT_ID>

Configure Argo CD Notifications
--------------------------------

Add a webhook service and a template to ``argocd-notifications-cm``:

.. code-block:: yaml

    service.webhook.robusta: |
      url: https://api.robusta.dev/webhooks?type=change&origin=argocd&account_id=<ACCOUNT_ID>
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

Subscribe applications to the trigger using the ``notifications.argoproj.io/subscribe.<trigger>.robusta`` annotation. Replace ``<trigger>`` with the trigger name you want to forward — for example, ``on-sync-failed``:

.. code-block:: yaml

    apiVersion: argoproj.io/v1alpha1
    kind: Application
    metadata:
      name: my-app
      namespace: argocd
      annotations:
        notifications.argoproj.io/subscribe.on-sync-failed.robusta: ""
        notifications.argoproj.io/subscribe.on-deployed.robusta: ""
        notifications.argoproj.io/subscribe.on-health-degraded.robusta: ""
    spec:
      # ...

The annotation value can be left empty (any non-null value subscribes the receiver) or set to a comma-separated list of recipients if you have configured multiple Robusta receivers.

Verify
------

Trigger a sync on a subscribed application. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
