Argo CD
========

Forward Argo CD application sync events to Robusta so HolmesGPT can
correlate deployments with alert spikes.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* `argocd-notifications-cm` installed in your Argo CD cluster (ships
  with Argo CD 2.3+).

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=change&origin=argocd&account_id=<ACCOUNT_ID>

Configure Argo CD
-----------------

Add a Robusta webhook service and a notification template to
``argocd-notifications-cm``:

.. code-block:: yaml

    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: argocd-notifications-cm
    data:
      service.webhook.robusta: |
        url: https://api.robusta.dev/webhooks?type=change&origin=argocd&account_id=<ACCOUNT_ID>
        headers:
        - name: Authorization
          value: "Bearer <ROBUSTA_API_KEY>"
        - name: Content-Type
          value: application/json
      template.app-change: |
        webhook:
          robusta:
            method: POST
            body: |
              {
                "app": "{{.app.metadata.name}}",
                "namespace": "{{.app.metadata.namespace}}",
                "project": "{{.app.spec.project}}",
                "syncStatus": "{{.app.status.sync.status}}",
                "healthStatus": "{{.app.status.health.status}}",
                "revision": "{{.app.status.sync.revision}}",
                "previousRevision": "{{(index .app.status.history (sub (len .app.status.history) 1)).revision}}",
                "repo": "{{.app.spec.source.repoURL}}",
                "path": "{{.app.spec.source.path}}",
                "cluster": "{{.app.spec.destination.name}}",
                "destNamespace": "{{.app.spec.destination.namespace}}",
                "operation": "{{.app.status.operationState.phase}}",
                "operationMessage": "{{.app.status.operationState.message}}",
                "startedAt": "{{.app.status.operationState.startedAt}}",
                "finishedAt": "{{.app.status.operationState.finishedAt}}"
              }
      trigger.on-sync-succeeded: |
        - when: app.status.operationState.phase in ['Succeeded']
          send: [app-change]

Subscribe the trigger on the Application:

.. code-block:: yaml

    metadata:
      annotations:
        notifications.argoproj.io/subscribe.on-sync-succeeded.robusta: ""

Example Payload
---------------

After Argo CD substitutes the template variables, Robusta receives:

.. code-block:: json

    {
      "app": "checkout",
      "namespace": "argocd",
      "project": "default",
      "syncStatus": "Synced",
      "healthStatus": "Healthy",
      "revision": "abc123",
      "previousRevision": "def456",
      "repo": "https://github.com/acme/checkout",
      "path": "deploy/",
      "cluster": "prod-eu-1",
      "destNamespace": "default",
      "operation": "Succeeded",
      "operationMessage": "sync completed"
    }

The parser produces a ``configuration_change`` Issue scoped to the
ArgoCD application, with a ``diff`` evidence row contrasting the
previous and current revisions.

Test the Integration
--------------------

Trigger a manual sync from the Argo CD UI. The event should appear on
the Robusta timeline within a few seconds.
