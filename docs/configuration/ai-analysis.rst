.. _ai-analysis-overview:

AI Analysis
==========================

Robusta can integrate with `Holmes GPT <https://github.com/robusta-dev/holmesgpt>`_ to analyze health issues on your cluster, and to run AI based root cause analysis for alerts.

Holmes can be installed with Robusta by adding ``enableHolmesGPT: true`` to the Robusta ``generated_values.yaml`` file.

When available, AI based investigations can be launched using the ``Ask Holmes`` button in Slack. The results will be sent back as a new message.

.. image:: /images/robusta-holmes-investigation.png
    :width: 600px

On the Robusta UI, clicking the ``Find Root Cause`` button will start an investigation and display its results.

.. image:: /images/ai-root-causeanalysis.png
    :width: 600px

Configuration
^^^^^^^^^^^^^^^^^^

.. warning::

  Only GPT-4o is officially supported. We highly recommend using GPT-4o to get the most accurate results!

In order to include ``Holmes GPT`` with you Robusta installation, add the following to your ``generated_values.yaml``

In the examples below, we're assuming you created a Kubernetes ``secret`` named ``holmes-secrets`` to store sensitive variables.

To use Open AI (this is the default llm):

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


To use Azure Open AI:

.. code-block:: yaml

    enableHolmesGPT: true
    holmes:
      additionalEnvVars:
      - name: MODEL
        value: azure/my-azure-deployment  # the name of your azure deployment
      - name: AZURE_API_VERSION
        value: 2024-02-15-preview
      - name: AZURE_API_BASE
        value: https://my-org.openai.azure.com/  # base url of you azure deployment
      - name: AZURE_API_KEY
        valueFrom:
          secretKeyRef:
            name: holmes-secrets
            key: azureOpenAiKey


To use Azure AI, follow the setup instructions below and then edit Robusta's Helm values. Do NOT skip the setup instructions, as they include a mandatory change rate-limits. Without this change, Holmes wont work.

.. details:: Mandatory Setup for Azure AI

  The following steps cover how to obtain the correct AZURE_API_VERSION value and how to increase the token limit to prevent rate limiting.

  1. Go to your Azure portal and choose `Azure OpenAI`
    .. image:: /images/AzureAI/AzureAI_HolmesStep1.png
        :width: 600px
  2. Click your AI service
    .. image:: /images/AzureAI/AzureAI_HolmesStep2.png
        :width: 600px
  3. Click Go to Azure Open AI Studio
    .. image:: /images/AzureAI/AzureAI_HolmesStep3.png
        :width: 600px
  4. Choose Deployments
    .. image:: /images/AzureAI/AzureAI_HolmesStep4.png
        :width: 600px
  5. Select your Deployment
    .. image:: /images/AzureAI/AzureAI_HolmesStep5.png
        :width: 600px
  6. Click Open in Playground
    .. image:: /images/AzureAI/AzureAI_HolmesStep6.png
        :width: 600px
  7. Go to View Code
    .. image:: /images/AzureAI/AzureAI_HolmesStep7.png
        :width: 600px
  8. Choose Python and scroll to find the API VERSION. Copy this! You will need it for Robusta's Helm values.
    .. image:: /images/AzureAI/AzureAI_HolmesStep8.png
        :width: 600px
  9. Go back to Deployments, and click Edit Deployment
    .. image:: /images/AzureAI/AzureAI_HolmesStep9.png
        :width: 600px
  10. MANDATORY: Increase the token limit. Change this value to at least 450K tokens for Holmes to work properly. We recommend choosing the highest value available. (Holmes queries Azure AI infrequently but in bursts. Therefore the overall cost of using Holmes with Azure AI is very low, but you must increase the quota to avoid getting rate-limited on a single burst of requests.)
    .. image:: /images/AzureAI/AzureAI_HolmesStep10.png
        :width: 600px


To use AWS Bedrock:

.. code-block:: yaml

    enableHolmesGPT: true
    holmes:
      enablePostProcessing: true
      additionalEnvVars:
      - name: MODEL
        value: bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0  # your bedrock model
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
