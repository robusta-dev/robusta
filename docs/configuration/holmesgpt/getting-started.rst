Getting Started
===============

Set up AI-powered alert analysis in 5 minutes.

Prerequisites
-------------

.. raw:: html

   <div style="margin: 20px 0; padding: 15px; background-color: #fff3e0; border-left: 4px solid #ff9800;">
   ✓ Robusta SaaS account (free or paid)<br>
   ✓ Robusta UI sink enabled<br>
   ✓ Robusta version 0.22.0 or higher
   </div>

Quick Setup (Recommended)
--------------------------

Use Robusta's hosted AI service with GPT-4o:

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

.. note::

   When exploring HolmesGPT documentation, focus on **Robusta Helm chart configuration** sections rather than CLI installation. Robusta users should follow the Robusta Helm Chart based configuration examples for data sources and advanced settings.

Test Your Setup
---------------

Deploy a crashing pod to see HolmesGPT in action:

.. code-block:: bash

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/crashpod/broken.yaml

Then check:
- **Robusta UI**: Look for the ``CrashLoopBackOff`` alert and click the "Root Cause" tab
- **Slack**: Click "Ask HolmesGPT" on the alert notification

Using Your Own AI Provider
---------------------------

Instead of Robusta AI, you can use your own OpenAI, Azure, or AWS Bedrock account.

.. tab-set::

    .. tab-item:: OpenAI
        
        .. code-block:: bash

            kubectl create secret generic holmes-secrets \
              --from-literal=openAiKey='YOUR_API_KEY'

        .. code-block:: yaml

            enableHolmesGPT: true
            holmes:
              additionalEnvVars:
              - name: MODEL
                value: gpt-4o
              - name: OPENAI_API_KEY
                valueFrom:
                  secretKeyRef:
                    name: holmes-secrets
                    key: openAiKey

    .. tab-item:: Azure AI
        
        .. code-block:: bash

            kubectl create secret generic holmes-secrets \
              --from-literal=azureOpenAiKey='YOUR_API_KEY'

        .. code-block:: yaml

            enableHolmesGPT: true
            holmes:
              additionalEnvVars:
              - name: MODEL
                value: azure/YOUR_DEPLOYMENT_NAME
              - name: AZURE_API_VERSION
                value: "2024-06-01"
              - name: AZURE_API_BASE
                value: https://your-org.openai.azure.com/
              - name: AZURE_API_KEY
                valueFrom:
                  secretKeyRef:
                    name: holmes-secrets
                    key: azureOpenAiKey

        **Important**: In Azure Portal, increase your deployment's token limit to at least 450K.

    .. tab-item:: AWS Bedrock
        
        .. code-block:: bash

            kubectl create secret generic holmes-secrets \
              --from-literal=awsAccessKeyId='YOUR_KEY_ID' \
              --from-literal=awsSecretAccessKey='YOUR_SECRET_KEY'

        .. code-block:: yaml

            enableHolmesGPT: true
            holmes:
              enablePostProcessing: true
              additionalEnvVars:
              - name: MODEL
                value: bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0
              - name: AWS_REGION_NAME
                value: us-east-1
              - name: AWS_ACCESS_KEY_ID
                valueFrom:
                  secretKeyRef:
                    name: holmes-secrets
                    key: awsAccessKeyId
              - name: AWS_SECRET_ACCESS_KEY
                valueFrom:
                  secretKeyRef:
                    name: holmes-secrets
                    key: awsSecretAccessKey

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
   - Enable additional data sources in `HolmesGPT data sources <https://holmesgpt.dev/data-sources/builtin-toolsets/>`_ (follow Helm chart configuration examples)
   - Ensure Prometheus is configured for metrics analysis
   - Check that pod logs are accessible

Next Steps
----------

* :doc:`main-features` - See what HolmesGPT can do
* `Configure Data Sources <https://holmesgpt.dev/data-sources/builtin-toolsets/>`_ - Add more context for better analysis (use Helm chart configuration)
* `Helm Configuration Reference <https://holmesgpt.dev/reference/helm-configuration/>`_ - Advanced HolmesGPT Helm settings