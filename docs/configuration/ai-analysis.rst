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

.. tab-set::

    .. tab-item:: Robusta
        :name: robusta-ai

        Update your helm values (``generated_values.yaml`` file) with the following configuration:

        .. code-block:: yaml

            enableHolmesGPT: true
            holmes:
              additionalEnvVars:
              - name: ROBUSTA_AI
                value: "true"

        Run Helm upgrade to apply the new values: ``helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>``

        .. note::

            The Robusta mode is available only when using the Robusta UI

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


        Do a Helm upgrade to apply the new values: ``helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>``


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

          5. Select your Deployment - note the DEPLOYMENT_NAME!

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
              - name: AZURE_API_VERSION
                value: <API_VERSION>            # replace with API version you found in the Azure portal
              - name: AZURE_API_BASE
                value: <AZURE_ENDPOINT>         # fill in the base endpoint url of your azure deployment - e.g. https://my-org.openai.azure.com/
              - name: AZURE_API_KEY
                valueFrom:
                  secretKeyRef:
                    name: holmes-secrets
                    key: azureOpenAiKey

        Do a Helm upgrade to apply the new values: ``helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>``

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

        Do a Helm upgrade to apply the new values: ``helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>``


Sinks Configuration Secrets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Holmes uses the ``token`` used for the ``Robusta UI sink``.
If you're pulling this ``token`` from a secret:

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

You should direct Holmes to use the same secret, and pass it as an environment variable named ``ROBUSTA_UI_TOKEN``:

.. code-block:: yaml

    holmes:
      additional_env_vars:
      ....
      - name: ROBUSTA_UI_TOKEN
        valueFrom:
          secretKeyRef:
            name: my-robusta-secrets
            key: ui-token


Test Holmes Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this section we will see Holmes in action by deploying a crashing pod and analyzing the alert with AI.

Before we proceed, you must follow the instructions above and configure Holmes.

1. Let's deploy a crashing pod to simulate an issue.

.. code-block:: yaml

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/crashpod/broken.yaml

2. Go to the **Timeline** in `platform.robusta.dev  <https://platform.robusta.dev/>`_ and click on the ``CrashLoopBackOff`` alert

.. image:: /images/AI_Analysis_demo.png
    :width: 1000px

3. Click the "Root Cause" tab on the top. This gives you the result of an investigation done by HolmesGPT based on the alert.

.. image:: /images/AI_Analysis_demo2.png
    :width: 1000px

Additionally your alerts on Slack will have an "Ask Holmes" button. Clicking it will give you results in the Slack channel itself. Note that due to technical limitations with Slack-buttons, alerts analyzed from Slack will be sent to the AI without alert-labels. For the most accurate results, it is best to use the UI.


Adding Custom Tools to Holmes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Holmes allows you to define custom toolsets that enhance its functionality by enabling additional tools to run Kubernetes commands or other tasks.

In this guide, we will show how to add a custom toolset to Holmes in your ``generated_values.yaml`` file.

Updating the Helm Values
----------------------------------------------------

To add a toolset in Holmes, update the ``generated_values.yaml`` with the following configuration:

.. code-block:: yaml

    enableHolmesGPT: true
    holmes:
      additionalEnvVars:
        - name: ROBUSTA_AI
          value: "true"
      toolsets:
        # Name of the toolset (for example "mycompany/internal-tools")
        # Used for informational purposes only (e.g. to print the name of the toolset if it can't be loaded)
        - name: "resource_explanation"
          # List of tools the LLM can use - this is the important part
          tools:
          # Name is a unique identifier for the tool
            - name: "explain_resource"
              # The LLM looks at this description when deciding what tools are relevant for each task
              description: "Provides detailed explanation of Kubernetes resources using kubectl explain"
              # A templated bash command using Jinja2 templates
              # The LLM can only control parameters that you expose as template variables like {{ resource_name }}
              command: "kubectl explain {{ resource_name }}"


``toolsets``: Defines a custom toolset, in this case, a ``resource_explanation``, which allows Holmes to use the ``kubectl explain`` command to provide details about various Kubernetes resources.

Applying the Changes
--------------------

Once you have updated the ``generated_values.yaml`` file, apply the changes by running the Helm upgrade command:

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

After the deployment, the custom toolset is automatically available for Holmes to use. Holmes will now be able to run the ``kubectl explain`` tool whenever required, allowing it to provide details about various Kubernetes resources.


Adding a tool that requires a new binary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some cases, adding a new tool to Holmes might require installing additional packages that are not included in the base Holmes Docker image. This guide explains how to create a custom Docker image that includes the new binaries and update your Helm deployment to use the custom image.

Creating a Custom Docker Image
--------------------------------------

To install a non-standard binary (such as ``jq`` for JSON processing) or any additional Linux tool, you can create a custom Docker image that inherits from the main Holmes image and installs the required binaries.

**Example Dockerfile to add jq:**

.. code-block:: bash

    FROM python:3.11-slim

    ENV PYTHONUNBUFFERED=1
    ENV PATH="/venv/bin:$PATH"
    ENV PYTHONPATH=$PYTHONPATH:.:/app/holmes

    WORKDIR /app

    COPY --from=builder /app/venv /venv
    COPY . /app

    # We're installing here libexpat1, to upgrade the package to include a fix to 3 high CVEs. CVE-2024-45491,CVE-2024-45490,CVE-2024-45492
    RUN apt-get update \
        && apt-get install -y \
        git \
        apt-transport-https \
        gnupg2 \
        && apt-get purge -y --auto-remove \
        && apt-get install -y --no-install-recommends libexpat1 \
        && rm -rf /var/lib/apt/lists/*

    # Example of installing jq
    RUN apt-get install -y jq


Build and Push the Custom Docker Image
----------------------------------------------

Now, you will need to **build and push** the Docker image to your container registry.

**Abstracted Instructions for Building and Pushing the Docker Image**:

1. **Build the Docker Image**:
   Depending on the tools and binaries you need, build the custom Docker image with the appropriate tag.

   .. code-block:: bash

       docker build -t <your-registry>/<your-project>/holmes-custom:<tag> .

   Replace:
   - ``<your-registry>``: Your Docker registry (e.g., ``us-central1-docker.pkg.dev`` for Google Artifact Registry).
   - ``<your-project>``: Your project or repository name.
   - ``<tag>``: The desired tag for the image (e.g., ``latest``, ``v1.0``).

2. **Push the Image to Your Registry**:
   After building the image, push it to your container registry:

   .. code-block:: bash

       docker push <your-registry>/<your-project>/holmes-custom:<tag>

   This ensures that the image is available for your Kubernetes deployment.

--------------------------------------------------

After pushing your custom Docker image, update your ``generated_values.yaml`` to use this custom image for Holmes.

.. code-block:: yaml

    enableHolmesGPT: true
    holmes:
      registry: <your-registry>/<your-project>  # Use your custom registry
      image: <image>:<tag>  # Specify the image with the tag you used when pushing the image
      additionalEnvVars:
        - name: ROBUSTA_AI
          value: "true"
      toolsets:
        - name: "json_processor"
          prerequisites:
            - command: "jq --version"  # Ensure jq is installed
          tools:
            - name: "process_json"
              description: "A tool that uses jq to process JSON input"
              command: "echo '{{ json_input }}' | jq '.'"  # Example jq command to format JSON

Update the Deployment with Helm
---------------------------------------

After updating your ``generated_values.yaml``, apply the changes to your Helm deployment:

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

This will update the deployment to use the custom Docker image, which includes the new binaries. The ``toolsets`` defined in the configuration will now be available for Holmes to use, including any new binaries like ``jq``.
