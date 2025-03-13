.. _ai-analysis-overview:

AI Analysis
============

.. toctree::
   :hidden:
   :maxdepth: 1

   builtin_toolsets
   permissions
   custom_toolsets

Why use HolmesGPT?
^^^^^^^^^^^^^^^^^^^

Robusta can integrate with `Holmes GPT <https://github.com/robusta-dev/holmesgpt>`_ to analyze health issues on your cluster, and to run AI based root cause analysis for alerts.

When available, AI based investigations can be launched in one of two ways:

1. Click the ``Ask Holmes`` button in Slack. The AI investigation will be sent back as a new message.

.. image:: /images/robusta-holmes-investigation.png
    :width: 600px

2. In the Robusta UI, click the ``Root Cause`` tab on an alert.

.. image:: /images/ai-root-causeanalysis.png
    :width: 600px

Configuring HolmesGPT
^^^^^^^^^^^^^^^^^^^^^^

Add ``enableHolmesGPT: true`` to the Robusta Helm values, and then follow these steps:

1. Choose an AI model - we highly recommend using GPT-4o to get the most accurate results! Other models may work, but are not officially supported.
2. :ref:`Configure your AI provider with the chosen model <Choosing and configuring an AI provider>`.
3. :ref:`Optional: Configure HolmesGPT Access to SaaS Data <Configuring HolmesGPT Access to SaaS Data>`.

Choosing and configuring an AI provider
----------------------------------------

Choose an AI provider below and follow the instructions:

.. tab-set::

    .. tab-item:: Robusta AI
        :name: robusta-ai

        Robusta AI is a premium AI service hosted by Robusta. To use Robusta AI, you must:

        1. :ref:`Have a Robusta account and enable the Robusta UI sink in Robusta's Helm values <Configuring the Robusta UI Sink>`.
        2. Add the following to your Helm values (``generated_values.yaml`` file) and run a :ref:`Helm Upgrade <Simple Upgrade>`

        .. code-block:: yaml

            enableHolmesGPT: true
            holmes:
              additionalEnvVars:
              - name: ROBUSTA_AI
                value: "true"

        3. If you store the Robusta UI token in a Kubernetes secret, follow the instructions in :ref:`Configuring HolmesGPT Access to SaaS Data <Configuring HolmesGPT Access to SaaS Data>`.

    .. tab-item:: OpenAI
        :name: open-ai

        Create a secret with your OpenAI API key:

        .. code-block:: bash

          kubectl create secret generic holmes-secrets --from-literal=openAiKey='<API_KEY_GOES_HERE>'

        Then add the following to your helm values (``generated_values.yaml`` file):

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

        Run a :ref:`Helm Upgrade <Simple Upgrade>` to apply the configuration.

    .. tab-item:: Azure AI
        :name: azure-ai

        Go into your Azure portal, **change the default rate-limit to the maximum**, and find the following parameters:

        * API_VERSION
        * DEPLOYMENT_NAME
        * ENDPOINT
        * API_KEY

        .. details:: Step-By-Step Instruction for Azure Portal

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

          5. Select your Deployment - note the DEPLOYMENT_NAME! Include 'gpt-4o' in the deployment name if you are using that model.

          .. image:: /images/AzureAI/AzureAI_HolmesStep5.png
              :width: 600px

          6. Click Open in Playground

          .. image:: /images/AzureAI/AzureAI_HolmesStep6.png
              :width: 600px

          7. Go to View Code

          .. image:: /images/AzureAI/AzureAI_HolmesStep7.png
              :width: 600px

          8. Choose Python and scroll to find the ENDPOINT, API_KEY, and API_VERSION. Copy them! You will need them for Robusta's Helm values.

          .. image:: /images/AzureAI/AzureAI_HolmesStep8.png
              :width: 600px

          9. Go back to Deployments, and click Edit Deployment

          .. image:: /images/AzureAI/AzureAI_HolmesStep9.png
              :width: 600px

          10. MANDATORY: Increase the token limit. Change this value to at least 450K tokens for Holmes to work properly. We recommend choosing the highest value available. (Holmes queries Azure AI infrequently but in bursts. Therefore the overall cost of using Holmes with Azure AI is very low, but you must increase the quota to avoid getting rate-limited on a single burst of requests.)

          .. image:: /images/AzureAI/AzureAI_HolmesStep10.png
              :width: 600px


        Create a secret with the Azure API key you found above:

        .. code-block:: bash

          kubectl create secret generic holmes-secrets --from-literal=azureOpenAiKey='<AZURE_API_KEY_GOES_HERE>'


        Update your helm values (``generated_values.yaml`` file) with the following configuration:

        .. code-block:: yaml

            enableHolmesGPT: true
            holmes:
              additionalEnvVars:
              - name: MODEL
                value: azure/<DEPLOYMENT_NAME>  # replace with deployment name from the portal (e.g. avi-deployment), leave "azure/" prefix
              - name: MODEL_TYPE
                value: gpt-4o                   # your azure deployment model type
              - name: AZURE_API_VERSION
                value: <API_VERSION>            # replace with API version you found in the Azure portal
              - name: AZURE_API_BASE
                value: <AZURE_ENDPOINT>         # fill in the base endpoint url of your azure deployment - e.g. https://my-org.openai.azure.com/
              - name: AZURE_API_KEY
                valueFrom:
                  secretKeyRef:
                    name: holmes-secrets
                    key: azureOpenAiKey

        Run a :ref:`Helm Upgrade <Simple Upgrade>` to apply the configuration.

    .. tab-item:: AWS Bedrock
        :name: aws-bedrock

        You will need the following AWS parameters:

        * BEDROCK_MODEL_NAME
        * AWS_ACCESS_KEY_ID
        * AWS_SECRET_ACCESS_KEY

        Create a secret with your AWS credentials:

        .. code-block:: bash

          kubectl create secret generic holmes-secrets --from-literal=awsAccessKeyId='<YOUR_AWS_ACCESS_KEY_ID>' --from-literal=awsSecretAccessKey'<YOUR_AWS_SECRET_ACCESS_KEY>'

        Update your helm values (``generated_values.yaml`` file) with the following configuration:

        .. code-block:: yaml

            enableHolmesGPT: true
            holmes:
              enablePostProcessing: true
              additionalEnvVars:
              - name: MODEL
                value: bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0  # your bedrock model - replace with your own exact model name
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

        Run a :ref:`Helm Upgrade <Simple Upgrade>` to apply the configuration.

Configuring HolmesGPT Access to SaaS Data
----------------------------------------------------

To use HolmesGPT with the Robusta UI, one further step may be necessary, depending on how Robusta is configured.

* If you define the Robusta UI token directly in your Helm values, HolmesGPT can read the token automatically and no further setup is necessary.
* If you store the Robusta UI token in a Kubernetes secret, follow the instructions below.

Note: the same Robusta UI token is used for the Robusta UI sink and for HolmesGPT.

Reading the Robusta UI Token from a secret in HolmesGPT
************************************************************

1. Review your existing Robusta Helm values - you should have an existing section similar to this, which reads the Robusta UI token from a secret:

.. code-block:: yaml

    runner:
      additional_env_vars:
      - name: UI_SINK_TOKEN
        valueFrom:
          secretKeyRef:
            name: my-robusta-secrets
            key: ui-token

    sinksConfig:
    - robusta_sink:
        name: robusta_ui_sink
        token: "{{ env.UI_SINK_TOKEN }}"

2. Add the following to your Helm values, directing HolmesGPT to use the same secret, passed as an environment variable named ``ROBUSTA_UI_TOKEN``:

.. code-block:: yaml

    holmes:
      additionalEnvVars:
      ....
      - name: ROBUSTA_UI_TOKEN
        valueFrom:
          secretKeyRef:
            name: my-robusta-secrets
            key: ui-token

Run a :ref:`Helm Upgrade <Simple Upgrade>` to apply the configuration.

Test Holmes Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this section we will see Holmes in action by deploying a crashing pod and analyzing the alert with AI.

Before we proceed, you must follow the instructions above and configure Holmes.

Once everything is setup:

1. Deploy a crashing pod to simulate an issue.

.. code-block:: yaml

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/crashpod/broken.yaml

2. Go to the **Timeline** in `platform.robusta.dev  <https://platform.robusta.dev/>`_ and click on the ``CrashLoopBackOff`` alert

.. image:: /images/AI_Analysis_demo.png
    :width: 1000px

3. Click the "Root Cause" tab on the top. This gives you the result of an investigation done by HolmesGPT based on the alert.

.. image:: /images/AI_Analysis_demo2.png
    :width: 1000px

Additionally your alerts on Slack will have an "Ask Holmes" button that sends an analysis back to Slack.

.. warning::

  Due to technical limitations with Slack, alerts analyzed from Slack will be sent to the AI without alert-labels.

  This means sometimes the AI won't know the namespace, pod name, or other metadata and the results may be less accurate.

  For the most accurate results, it is best to use the Robusta UI.


Adding data sources to HolmesGPT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

HolmesGPT's toolsets are fundamental to its ability to investigate and diagnose Kubernetes
cluster issues effectively. Each toolset provides specialized capabilities for gathering
and analyzing specific aspects of cluster health, performance, and configuration.

The more toolsets available to HolmesGPT, the more comprehensive and nuanced its investigation
process becomes, enabling it to identify complex issues through multiple perspectives and provide
more accurate, actionable recommendations for resolution.

Builtin toolsets
----------------

:doc:`Follow this link <builtin_toolsets>` to learn how to configure builtin toolsets.

Built-in toolsets cover essential areas like pod status inspection, node health analysis,
application diagnostics, and resource utilization monitoring. These toolsets include access to
Kubernetes events and logs, AWS, Grafana, Opensearch, etc. See the full list :doc:`here <builtin_toolsets>`.

Custom toolsets
----------------

.. include:: ./toolsets/_custom_toolset_appeal.inc.rst

Custom toolsets are created through your Helm values file and you can find instructions
to :doc:`write your own toolsets here <builtin_toolsets>`.
