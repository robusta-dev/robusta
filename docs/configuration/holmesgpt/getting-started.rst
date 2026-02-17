Getting Started
===============

Set up AI-powered alert analysis in 5 minutes.

Prerequisites
-------------

.. raw:: html

   <div style="margin: 20px 0; padding: 15px; background-color: #fff3e0; border-left: 4px solid #ff9800;">
   ✓ <a href="https://platform.robusta.dev/signup">Robusta SaaS account</a> (free or paid)<br>
   ✓ Robusta version 0.22.0 or higher
   </div>

Quick Setup (Recommended)
--------------------------

Use Robusta's hosted AI service with frontier models from Anthropic, OpenAI, and more:

1. **Add to your Helm values:**

   .. code-block:: yaml

       enableHolmesGPT: true
       holmes:
         additionalEnvVars:
         - name: ROBUSTA_AI
           value: "true"

2. **Apply the changes:**

   .. code-block:: bash

       helm upgrade robusta robusta/robusta -f generated_values.yaml

3. **Enable Slack integration** (optional):
   
   - Go to `platform.robusta.dev <https://platform.robusta.dev>`_
   - Navigate to **Settings** → **AI Assistant**
   - Toggle "Enable Holmes" and connect your Slack workspace

That's it! HolmesGPT will now analyze your alerts automatically.

Using Your Own AI Provider
---------------------------

Instead of Robusta AI, you can bring your own LLM provider (OpenAI, Azure, AWS Bedrock, Anthropic, and more). See the `AI Providers documentation <https://holmesgpt.dev/ai-providers/?tab=robusta-helm-chart>`_ for setup instructions.

.. _Reading the Robusta UI Token from a secret in HolmesGPT:

Using Existing Secrets
----------------------

If you store the Robusta UI token in a Kubernetes secret (instead of directly in Helm values), you need to pass it to HolmesGPT:

.. code-block:: yaml

    holmes:
      additionalEnvVars:
      - name: ROBUSTA_UI_TOKEN
        valueFrom:
          secretKeyRef:
            name: my-robusta-secrets  # Your existing secret
            key: ui-token             # Your existing key

Common Issues
-------------

**Not seeing the "Ask HolmesGPT" button?**
   - Ensure ``enableHolmesGPT: true`` is set
   - Check HolmesGPT pod is running: ``kubectl get pods -n robusta | grep holmes``
   - Verify AI provider credentials are correct

**Getting rate limit errors?**
   - Azure: Increase token limit in Azure Portal (minimum 450K)
   - OpenAI: Check your API quota and billing
   - Consider using Robusta AI for unlimited investigations

**Analysis seems incomplete?**
   - Enable additional data sources in `HolmesGPT data sources <https://holmesgpt.dev/data-sources/builtin-toolsets/?tab=robusta-helm-chart>`_
   - Ensure Prometheus is configured for metrics analysis
   - Check that pod logs are accessible

Next Steps
----------

* :doc:`main-features` - See what HolmesGPT can do
* `Configure Data Sources <https://holmesgpt.dev/data-sources/builtin-toolsets/?tab=robusta-helm-chart>`_ - Add more context for better analysis
* `Helm Configuration Reference <https://holmesgpt.dev/reference/helm-configuration/?tab=robusta-helm-chart>`_ - Advanced HolmesGPT Helm settings