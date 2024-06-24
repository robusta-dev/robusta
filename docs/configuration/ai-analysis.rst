.. _ai-analysis-overview:

AI Analysis
==========================

Robusta can integrate with `Holmes GPT <https://github.com/robusta-dev/holmesgpt>`_ to analyze health issues on your cluster, and to run AI based root cause analysis for alerts.

Holmes can be installed with Robusta by adding ``enableHolmesGPT: true`` to the Robusta ``generated_values.yaml`` file.

When available, AI based investigations can be launched from a button in Slack, or from the Robusta UI.

When enabled, your Slack messages will have the ``Ask Holmes`` button:

   .. image:: /images/pod-pending-alert.png
       :width: 600px

Clicking it, will launch a Holmes investigation, which will send the results back to Slack:

   .. image:: /images/pending-alert-holmes-response.png
       :width: 600px


Configuration
^^^^^^^^^^^^^^^^^^

In order to include ``Holmes GPT`` with you Robusta installation, add the following to your ``generated_values.yaml``

To use Open AI (this is the default llm):

.. code-block:: yaml

    enableHolmesGPT: true
    holmes:
      openaiKey: <YOUR OPEN AI KEY>


To use Azure Open AI:

.. code-block:: yaml

    enableHolmesGPT: true
    holmes:
      llm: azure
      azureOpenaiKey: <YOUR AZURE OPEN AI KEY>
      azureEndpoint: <YOUR AZURE OPEN AI ENDPOINT>  # For example: ‘https://some-azure-org.openai.azure.com/openai/deployments/gpt4-1106/chat/completions?api-version=2023-07-01-preview’
