Webhook
###########

Robusta can report issues and events in your Kubernetes cluster to a webhook.

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - webhook_sink:
            name: webhook_sink
            url: "https://my-webhook-service.com/robusta-alerts"

Save the file and run

.. code-block:: bash
   :name: cb-add-webhook-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

**Example Output:**

.. admonition:: This example is sending Robusta notifications to ntfy.sh, push notification service

    .. image:: /images/deployment-babysitter-webhook.png
      :width: 600
      :align: center

Configuration parameters
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Default
     - Description
   * - ``url``
     - *(required)*
     - The webhook endpoint to POST to.
   * - ``format``
     - ``text``
     - Payload format. ``text`` for a human-readable body, ``json`` for a structured body.
   * - ``size_limit``
     - ``4096``
     - Maximum payload size in bytes. Content beyond the limit is truncated.
   * - ``authorization``
     - *(none)*
     - Optional value sent in the ``Authorization`` request header.
   * - ``slack_webhook``
     - ``false``
     - When ``true`` and ``format: json``, posts a Slack-compatible body for use with Slack incoming webhooks.

JSON payload
-------------

When ``format: json`` is set, the POST body is a JSON object with the following top-level fields:

.. robusta-code:: json

    {
      "title": "CrashLoopBackOff",
      "description": "Container is crashing repeatedly",
      "cluster_name": "prod-eu-west",
      "account_id": "abcd-1234",
      "severity": "HIGH",
      "source": "KUBERNETES_API_SERVER",
      "finding_type": "ISSUE",
      "aggregation_key": "CrashLoopBackOff",
      "failure": true,
      "fingerprint": "2c1d...",
      "starts_at": "2026-04-30T10:15:00+00:00",
      "ends_at": null,
      "subject": {
        "name": "my-pod",
        "kind": "pod",
        "namespace": "default",
        "node": "node-1",
        "container": "main",
        "labels": {"app": "demo"},
        "annotations": {"team": "platform"}
      },
      "links": [
        {"name": "Runbook", "url": "https://...", "type": null},
        {"name": "Graph",   "url": "https://...", "type": "prometheus_generator_url"}
      ],
      "investigate": "https://platform.robusta.dev/...",
      "silence": "https://platform.robusta.dev/silences/create?...",
      "enrichments": [ ... ]
    }

``investigate`` and ``silence`` are present only when the Robusta platform is enabled
(``silence`` additionally requires ``add_silence_url`` on the finding).

If the serialized payload exceeds ``size_limit``, the largest field (``enrichments``)
is dropped first so that core metadata and ``links`` survive truncation.
