.. _holmes-only-install:

Holmes-Only Install (Without the Runner)
========================================

The ``robusta`` chart can install HolmesGPT alone, without the Robusta runner or kubewatch.
Holmes connects to the Robusta platform directly, so Ask Holmes, Triggered Workflows, alert
triage and scheduled prompts work for the cluster.

Setting ``runner.enabled: false`` turns this on. The default is ``true``, so existing installs
are unchanged.

Values
------

Start from your ``generated_values.yaml`` and add:

.. code-block:: yaml

    runner:
      enabled: false
    kubewatch:
      enabled: false
    enableHolmesGPT: true

    clusterName: my-cluster
    globalConfig:
      account_id: <ACCOUNT_ID>
      signing_key: <SIGNING_KEY>
    sinksConfig:
      - robusta_sink:
          name: robusta_ui_sink
          token: <ROBUSTA_UI_TOKEN>

    holmes:
      additionalEnvVars:
        - name: ROBUSTA_AI
          value: "true"

The chart still renders ``robusta-playbooks-config-secret``, with only the cluster name,
account id, signing key and robusta sink. Holmes reads its platform credentials from it. Rendering
fails if ``enableHolmesGPT`` is false or if there is no ``robusta_sink``. Other sinks are
ignored, because only the runner uses them.

If the sink token is a reference such as ``{{ env.UI_SINK_TOKEN }}``, the variable must be set on
Holmes, not on the runner. Add it under ``holmes.additionalEnvVars``:

.. code-block:: yaml

    holmes:
      additionalEnvVars:
        - name: UI_SINK_TOKEN
          valueFrom:
            secretKeyRef:
              name: <SECRET_NAME>
              key: <SECRET_KEY>

Sending alerts
--------------

With no runner, there is no in-cluster ``<release>-runner`` endpoint for Alertmanager. Send alerts to
the Robusta platform directly instead. See :doc:`Send alerts from AlertManager
</configuration/exporting/send-events/alertmanager>`.

If you use the bundled Prometheus stack (``enablePrometheusStack: true``), its default ``robusta``
receiver points at the runner, and rendering fails until you replace it:

.. robusta-code:: yaml

    kube-prometheus-stack:
      alertmanager:
        config:
          receivers:
            - name: 'null'
            - name: robusta
              webhook_configs:
                - url: 'https://api.robusta.dev/webhooks?type=alert&origin=alertmanager&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>'
                  send_resolved: true
                  http_config:
                    authorization:
                      type: Bearer
                      credentials: <ROBUSTA_API_KEY>
