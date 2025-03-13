
Custom toolsets
===============

.. include:: ./toolsets/_custom_toolset_appeal.inc.rst

Examples
--------

Below are examples of custom toolsets and how to add them to Holmes:


Example 1: Grafana Toolset
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This toolset lets Holmes view Grafana dashboards and suggest relevant dashboards to the user:

**Prerequisites:**

- Grafana URL (e.g. http://localhost:3000 or https://grafana.example.com)
- Grafana service account token with **Basic role -> Viewer** and **Data sources -> Reader** permissions. Check out this `video <https://www.loom.com/share/f969ab3af509444693802254ab040791?sid=aa8b3c65-2696-4f69-ae47-bb96e8e03c47>`_ on creating a Grafana service account token.

**Configuration:**

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    **Helm Values:**

    .. code-block:: yaml

      holmes:
        # provide environment variables the toolset needs - can be pulled from secrets or provided in plaintext
        additionalEnvVars:
        - name: GRAFANA_API_KEY
          value: <token_goes_here>
        - name: GRAFANA_URL
          value: <grafana_url>

        # define the toolset
        toolsets:
          grafana:
            # this tool can only be enabled if these prerequisites are met
            prerequisites:
              # we need the GRAFANA_URL and GRAFANA_API_KEY environment variables to be set
              - env:
                  - "GRAFANA_URL"
                  - "GRAFANA_API_KEY"
              # curl must be installed - we check by running `curl --version` (if it's not installed, the command will fail)
              - command: "curl --version"

            # human-readable description of the toolset (this is not seen by the AI model - its just for users)
            description: "Grafana tools"

            # tools (capabilities) that will be provided to HolmesGPT when this toolset is enabled
            tools:
            - name: "grafana_get_dashboard"
              # the LLM sees this description and uses it to decide when to use this tool
              description: "Get list of grafana dashboards"
              # the command that will be executed when this tool is used
              # environment variables like GRAFANA_URL and GRAFANA_API_KEY can be used in the command
              # they will not be exposed to the AI model, as the AI model doesn't see the command that was run
              command: "curl \"${GRAFANA_URL}/api/search\" -H \"Authorization: Bearer ${GRAFANA_API_KEY}\""

            - name: "grafana_get_url"
              description: "Get the URL of a Grafana dashboard by UID, including the real URL of Grafana"
              # in this command we use a variable called `{{ dashboard_uid }}`
              # unlike enviroment variables that were provided by the user, variables like `{{ dashboard_uid }}` are provided by the AI model
              # the AI model sees the tool description, decides to use this tool, and then provides a value for all {{ template_variables }} to invoke the tool
              command: "echo \"${GRAFANA_URL}/d/{{ dashboard_uid }}\""
        
    Update your Helm values with the provided YAML configuration, then apply the changes with Helm upgrade:

    .. code-block:: bash

        helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

    After the deployment is complete, you can open the HolmesGPT chat in the Robusta SaaS UI and ask questions like *what grafana dashboard should I look at to investigate high pod cpu?*.
    
    **Suggesting relevant dashboards during alert investigations:** Add runbook instructions to your alert in the Robusta UI, instructing Holmes to search for related Grafana dashboards.
  
    .. image:: /images/custom-grafana-toolset.png
        :width: 600
        :align: center

  .. md-tab-item:: Holmes CLI

    **grafana_toolset.yaml:**

    .. code-block:: yaml

      toolsets:
        grafana:
          # this tool can only be enabled if these prerequisites are met
          prerequisites:
            # we need the GRAFANA_URL and GRAFANA_API_KEY environment variables to be set
            - env:
                - "GRAFANA_URL"
                - "GRAFANA_API_KEY"
            # curl must be installed - we check by running `curl --version` (if it's not installed, the command will fail)
            - command: "curl --version"

          # human-readable description of the toolset (this is not seen by the AI model - its just for users)
          description: "Grafana tools"

          # tools (capabilities) that will be provided to HolmesGPT when this toolset is enabled
          tools:
          - name: "grafana_get_dashboard"
            # the LLM sees this description and uses it to decide when to use this tool
            description: "Get list of grafana dashboards"
            # the command that will be executed when this tool is used
            # environment variables like GRAFANA_URL and GRAFANA_API_KEY can be used in the command
            # they will not be exposed to the AI model, as the AI model doesn't see the command that was run
            command: "curl \"${GRAFANA_URL}/api/search\" -H \"Authorization: Bearer ${GRAFANA_API_KEY}\""

          - name: "grafana_get_url"
            description: "Get the URL of a Grafana dashboard by UID, including the real url of grafana"
            # in this command we use a variable called `{{ dashboard_uid }}`
            # unlike enviroment variables that were provided by the user, variables like `{{ dashboard_uid }}` are provided by the AI model
            # the AI model sees the tool description, decides to use this tool, and then provides a value for all {{ template_variables }} to invoke the tool
            command: "echo \"${GRAFANA_URL}/d/{{ dashboard_uid }}\""

    Set the appropriate environment variables and run Holmes:

    .. code-block:: bash

        export GRAFANA_API_KEY="<grafana_api_key>"
        export GRAFANA_URL="<grafana_url>"
      
    To test, run: 

    .. code-block:: bash

        holmes ask -t grafana_toolset.yaml "what grafana dashboard should I look at to investigate high pod cpu?"

Example 2: Kubernetes Diagnostics Toolset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This toolset provides diagnostics for Kubernetes clusters, helping developers identify and resolve issues.

.. code-block:: yaml

    holmes:
      toolsets:
        kubernetes/diagnostics:
          description: "Advanced diagnostics and troubleshooting tools for Kubernetes clusters"
          docs_url: "https://kubernetes.io/docs/home/"
          icon_url: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRPKA-U9m5BxYQDF1O7atMfj9EMMXEoGu4t0Q&s"
          tags:
            - core
            - cluster
          prerequisites:
            - command: "kubectl version --client"
          tools:

            - name: "kubectl_node_health"
              description: "Check the health status of all nodes in the cluster."
              command: "kubectl get nodes -o wide"

            - name: "kubectl_check_resource_quota"
              description: "Fetch the resource quota for a specific namespace."
              command: "kubectl get resourcequota -n {{ namespace }} -o yaml"

            - name: "kubectl_find_evicted_pods"
              description: "List all evicted pods in a specific namespace."
              command: "kubectl get pods -n {{ namespace }} --field-selector=status.phase=Failed | grep Evicted"

Update the ``generated_values.yaml`` file with the provided YAML configuration, then apply the changes by executing the Helm upgrade command:

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

Once deployed, Holmes will have access to advanced diagnostic tools for Kubernetes clusters. For example, you can ask Holmes, ``"Can you do a node health check?"`` and it will automatically use the newly added tools to provide you the answer.


Example 3: GitHub Toolset
^^^^^^^^^^^^^^^^^^^^^^^^^

This toolset enables Holmes to fetch information from GitHub repositories.

First `create a GitHub Personal Access Token with fine-grained permissions <https://github.com/settings/personal-access-tokens>`_. For this example, you can leave the default permissions.

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    **Helm Values:**

    .. code-block:: yaml

        holmes:
          # provide environment variables the toolset needs
          additionalEnvVars:
          - name: GITHUB_TOKEN
            value: <token_goes_here>

          # define the toolset itself
          toolsets:
            github_tools:
              description: "Tools for managing GitHub repositories"
              tags:
                - cli
              prerequisites:
                - env:
                  - "GITHUB_TOKEN"
                - command: "curl --version"
              tools:
                - name: "get_recent_commits"
                  description: "Fetches the most recent commits for a repository"
                  command: "curl -H 'Authorization: token ${GITHUB_TOKEN}' https://api.github.com/repos/{{ owner }}/{{ repo }}/commits?per_page={{ limit }} "

              - name: "get_repo_details"
                description: "Fetches details of a specific repository"
                command: "curl -H 'Authorization: token ${GITHUB_TOKEN}' https://api.github.com/repos/{{ owner }}/{{ repo }}"

                # In the above examples, LLM-provided parameters like {{ owner }} are inferred automatically from the command
                # you can also define them explicitly - this is useful if:
                # - You want to enforce parameter requirements (e.g., `owner` and `repo` are required).
                # - You want to define provide a default value for optional parameters.
                parameters:
                  owner:
                    type: "string"
                    description: "Owner of the repository."
                    required: true
                  repo:
                    type: "string"
                    description: "Name of the repository."
                    required: true

    Update your Helm values with the provided YAML configuration, then apply the changes with Helm upgrade:

    .. code-block:: bash

        helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

    After the deployment is complete, the GitHub toolset will be available. HolmesGPT will be able to use it to interact with GitHub repositories.
    For example, you can now open the HolmesGPT chat in the Robusta SaaS UI and ask, *who made the last commit to the robusta-dev/holmesgpt repo on github?*.

    .. image:: /images/custom-github-toolset.png
      :width: 600
      :align: center

  .. md-tab-item:: Holmes CLI

    First, add the following environment vairables:

    .. code-block:: bash
      
        export GITHUB_TOKEN="<token_goes_here>"

    Then, add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

        toolsets:
          github_tools:
            description: "Tools for managing GitHub repositories"
            tags:
              - cli
            prerequisites:
              - env:
                - "GITHUB_TOKEN"
              - command: "curl --version"
            tools:
              - name: "get_recent_commits"
                description: "Fetches the most recent commits for a repository"
                command: "curl -H 'Authorization: token ${GITHUB_TOKEN}' https://api.github.com/repos/{{ owner }}/{{ repo }}/commits?per_page={{ limit }} "

                # In the above examples, LLM-provided parameters like {{ owner }} are inferred automatically from the command
                # you can also define them explicitly - this is useful if:
                # - You want to enforce parameter requirements (e.g., `owner` and `repo` are required).
                # - You want to define provide a default value for optional parameters.
                parameters:
                  owner:
                    type: "string"
                    description: "Owner of the repository."
                    required: true
                  repo:
                    type: "string"
                    description: "Name of the repository."
                    required: true
    To test, run: 

      .. code-block:: yaml
        
        holmes ask -t github_toolset.yaml "who made the last commit to the robusta-dev/holmesgpt repo on github?"


Reference
---------

A toolset is defined in your Helm values (``generated_values.yaml``). Each toolset has a unique name and has to contain tools.


.. code-block:: yaml

    toolsets:
      <toolset_name>:
        enabled: <true|false>
        name: "<string>"
        description: "<string>"
        docs_url: "<string>"
        icon_url: "<string>"
        tags:
          - <cli|cluster|core>
        installation_instructions: "<string>"
        prerequisites:
          - command: "<shell_command>"
            expected_output: "<expected output of the command>"
          - env:
            - "<environment variable>"
        additional_instructions: "<string>"
        tools:
          - name: "<string>"
            description: "<string>"
            command: "<shell command template>"
            script: "<script content>"
            parameters:
              <parameter_name>:
                type: "<string>"
                description: "<string>"
                required: <true|false>

Toolset Fields
^^^^^^^^^^^^^^

.. list-table::
   :widths: 20 10 60 10
   :header-rows: 1

   * - **Parameter**
     - **Type**
     - **Description**
     - **Required**
   * - ``enabled``
     - boolean
     - Indicates whether the toolset is enabled. Defaults to ``true``. If set to ``false``, the toolset will be disabled.
     - No
   * - ``name``
     - string
     - A unique identifier for the toolset. Used for informational purposes and logging.
     - **Yes**
   * - ``description``
     - string
     - A summary of the toolset's purpose. This description is visible to the LLM and helps it decide when to use the toolset for specific tasks.
     - No
   * - ``docs_url``
     - string
     - A URL pointing to documentation related to the toolset.
     - No
   * - ``icon_url``
     - string
     - A URL to an icon representing the toolset.
     - No
   * - ``tags``
     - list
     - Tags for categorizing toolsets, ``core`` will be used for all Holmes features (both cli's commands and chats in UI). The ``cluster`` tag is used for UI functionality, while ``cli`` is for for command-line specific tools. Default to ``[core,]``.
     - No
   * - ``installation_instructions``
     - string
     - Instructions on how to install prerequisites required by the toolset.
     - No
   * - ``prerequisites``
     - list
     - A list of conditions that must be met for the toolset to be enabled. Prerequisites can include commands or environment variables, or both.
     - No
   * - ``additional_instructions``
     - string
     - Additional shell commands or processing instructions applied to the output of tools in this toolset.
     - No
   * - ``tools``
     - list
     - A list of tools defined within the toolset. Each tool is an object with its own set of fields.
     - **Yes**


**Tool Fields**

.. list-table::
   :widths: 20 10 60 10
   :header-rows: 1

   * - **Parameter**
     - **Type**
     - **Description**
     - **Required**
   * - ``name``
     - string
     - A unique identifier for the tool within the toolset.
     - **Yes**
   * - ``description``
     - string
     - A brief description of the tool's purpose. Helps Holmes decide when to use this tool.
     - **Yes**
   * - ``command``
     - string
     - A shell command template that the tool will execute. Can include environment variables using ``${ENV_VAR}`` or parameters that the LLM will fill in, using Jinja2 syntax (``{{ param_name }}``).
     - Either ``command`` or ``script`` is required
   * - ``script``
     - string
     - The content of a script that the tool will execute. Use this if your tool requires a multi-line script.
     - Either ``command`` or ``script`` is required
   * - ``parameters``
     - dictionary
     - Specifying parameters is optional, as they can be inferred by the LLM from the prompt context. When defined, parameters specify the inputs required for the tool, allowing dynamic customization of its execution. Each parameter has its own fields, such as type, description, and whether it is required.
     - No
   * - ``additional_instructions``
     - string
     - Additional shell commands or processing instructions applied to the output of this tool. This is can be useful for post-processing the results of a command, such as filtering, formatting, or transforming the data before it is returned to the user. For example, you could use ``"jq '.items[] | {reason, message}'"`` to extract and display specific fields (``reason`` and ``message``) from JSON output.
     - No


**Parameter Fields (Within `parameters`, if missing we infer it)**

.. list-table::
   :widths: 20 10 60 10
   :header-rows: 1

   * - **Parameter**
     - **Type**
     - **Description**
     - **Required**
   * - ``type``
     - string
     - The data type of the parameter (e.g., ``string``, ``integer``).
     - No (defaults to ``string``)
   * - ``description``
     - string
     - A description of the parameter.
     - No
   * - ``required``
     - boolean
     - Indicates whether the parameter is required. Defaults to ``true``.
     - No

Variable Syntax in Commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^

In toolset commands, variables can be defined using two syntaxes: ``{{ }}`` and ``${ }``.

Variables written as ``{{ variable_name }}`` are placeholders that are inferred by Holmes and dynamically filled by the LLM based on the context or user prompts. These variables are visible to the LLM and allow flexible, context-aware execution. For example:

.. code-block:: bash

  command: "kubectl describe pod {{ pod_name }} -n {{ namespace }}"


Here, ``{{ pod_name }}`` and ``{{ namespace }}``` are inferred and dynamically filled during execution.

Variables written as ``${VARIABLE_NAME}`` are static or environment-specific values, such as API keys or configuration parameters. These are not visible to the LLM and are expanded directly by the shell at runtime. For example:

.. code-block:: bash

    command: "curl -H 'Authorization: token ${GITHUB_TOKEN}' https://api.github.com/repos/{{ owner }}/{{ repo }}"


In this case, ``${GITHUB_TOKEN}`` is an environment variable, while ``{{ owner }}`` and ``{{ repo }}`` are dynamically inferred by Holmes.

**Best Practices for Variable Usage**:

* Use ``${}`` for sensitive or static environment variables, such as API keys and credentials.
* Use ``{{}}`` for parameters that the LLM can dynamically infer and fill based on the context or user inputs.


Adding a tool that requires a new binary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some cases, adding a new tool to Holmes might require installing additional packages that are not included in the base Holmes Docker image. This guide explains how to create a custom Docker image that includes the new binaries and update your Helm deployment to use the custom image.

As an example, we'll add a new HolmesGPT tool that uses the ``jq`` binary, which isn't present in the original image:

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
        json_processor:
          description: "A toolset for processing JSON data using jq"
          prerequisites:
            - command: "jq --version"  # Ensure jq is installed
          tools:
            - name: "process_json"
              description: "A tool that uses jq to process JSON input"
              command: "echo '{{ json_input }}' | jq '.'"  # Example jq command to format JSON


Finally, after updating your ``generated_values.yaml``, apply the changes to your Helm deployment:

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

This will update the deployment to use the custom Docker image, which includes the new binaries. The ``toolsets`` defined in the configuration will now be available for Holmes to use, including any new binaries like ``jq``.
