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
