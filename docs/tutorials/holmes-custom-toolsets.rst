Adding Custom Tools to Holmes
#########################

Holmes allows you to define custom toolsets that enhance its functionality by enabling additional tools to run Kubernetes commands or other tasks.

In this guide, we will show how to add a custom toolset to Holmes in your ``generated_values.yaml`` file.

Updating the Helm Values (``generated_values.yaml``)
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


**``toolsets``**: Defines a custom toolset, in this case, a ``resource_explanation``, which allows Holmes to use the ``kubectl explain`` command to provide details about various Kubernetes resources.

Applying the Changes
--------------------

Once you have updated the ``generated_values.yaml`` file, apply the changes by running the Helm upgrade command:

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

After the deployment, the custom toolset is automatically available for Holmes to use. Holmes will now be able to run the ``switch_cluster`` tool whenever required, allowing it to switch between Kubernetes contexts based on the defined parameters.

Adding a Tool that requires to update Holmes image
==================================================

In some cases, adding a new tool to Holmes might require installing additional packages that are not included in the base Holmes Docker image. This guide explains how to create a custom Docker image that includes the new binaries and update your Helm deployment to use the custom image.

Step 1: Creating a Custom Docker Image
--------------------------------------

To install a non-standard binary (such as ``jq`` for JSON processing) or any additional Linux tool, you can create a custom Docker image that inherits from the main Holmes image and installs the required binaries.

**Example Dockerfile to add ``jq``:**

.. code-block:: Dockerfile
    ...
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

    # Just an example
    RUN apt-get install -y jq
    ...

Step 2: Build and Push the Custom Docker Image
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

Step 4: Update the Deployment with Helm
---------------------------------------

After updating your ``generated_values.yaml``, apply the changes to your Helm deployment:

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

This will update the deployment to use the custom Docker image, which includes the new binaries. The ``toolsets`` defined in the configuration will now be available for Holmes to use, including any new binaries like ``jq``.
