Remote MCP Servers 
====================

.. warning::

    Remote MCP servers are in **Tech Preview** stage.


HolmesGPT can integrate with remote MCP servers using SSE mode.
This capability enables HolmesGPT to access external data sources and tools in real time.
This guide provides step-by-step instructions for configuring HolmesGPT to connect with remote MCP servers over SSE.

Example : MCP server configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    **Helm Values:**

    .. code-block:: yaml

      holmes:
        mcp_servers:
          mcp_server_1:
            # human-readable description of the mcp server (this is not seen by the AI model - its just for users)
            description: "Remote mcp server"
            url: "http://example.com:8000/sse"
          
          mcp_server_2:
            description: "MCP server that runs in my cluster"
            url: "http://<service-name>.<namespace>.svc.cluster.local:<service-port>"
            config:
              headers:
                key: "{{ env.my_mcp_server_key }}" # You can use holmes environment variables as headers for the MCP server requests.
        
    Update your Helm values with the provided YAML configuration, then apply the changes with Helm upgrade:

    .. code-block:: bash

        helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>


Example : Working with Stdio MCP servers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

MCP currently supports three transport mechanisms: stdio, Server-Sent Events (SSE), and Streamable HTTP.
At this time, HolmesGPT is compatible only with MCP servers that use SSE.
However, many existing MCP servers—such as Dynatrace MCP—rely exclusively on the stdio transport.
To overcome this incompatibility, tools like Supergateway can act as a bridge by converting stdio-based MCPs into SSE-compatible endpoints.

For this demo we will use
  * `Dynatrace MCP <https://github.com/dynatrace-oss/dynatrace-mcp>`_ .
  * `Supergateway <https://github.com/supercorp-ai/supergateway>`_ - runs MCP stdio-based servers over SSE.

Check out supergatway docs to find out other useful flags.

**See it in action** 

.. raw:: html

  <div>
      <a href="https://www.loom.com/share/1b290511b79942c7b1d672a2a4cde105">
        <img style="max-width:300px;" src="https://cdn.loom.com/sessions/thumbnails/1b290511b79942c7b1d672a2a4cde105-ed4eed3f9d70b125-full-play.gif">
      </a>
  </div>

1. Run stdio MCP as SSE
""""""""""""""""""""""""""""""
.. md-tab-set::

  .. md-tab-item:: Docker 
    
    This command runs the Dynatrace MCP server locally via Docker using Supergateway to wrap it with SSE support.
    Credentials (e.g., API keys) should be stored in a .env file passed to Docker using --env-file.
    you can change `"npx -y @dynatrace-oss/dynatrace-mcp-server@latest /"` to your specific MCP.

    .. code-block:: shell

      docker run --env-file .env -it --rm -p  8003:8003 supercorp/supergateway \
      --stdio "npx -y @dynatrace-oss/dynatrace-mcp-server@latest /" \
      --port 8003 \
      --logLevel debug 

    Once the container starts, you should see logs similar to:

    .. code-block:: shell

      [supergateway] Starting...
      [supergateway] Supergateway is supported by Supermachine (hosted MCPs) - https://supermachine.ai
      [supergateway]   - outputTransport: sse
      [supergateway]   - Headers: (none)
      [supergateway]   - port: 8003
      [supergateway]   - stdio: npx -y @dynatrace-oss/dynatrace-mcp-server@latest /
      [supergateway]   - ssePath: /sse
      [supergateway]   - messagePath: /message
      [supergateway]   - CORS: disabled
      [supergateway]   - Health endpoints: (none)
      [supergateway] Listening on port 8003
      [supergateway] SSE endpoint: http://localhost:8003/sse
      [supergateway] POST messages: http://localhost:8003/message

  .. md-tab-item:: Kubernetes Pod
    
    | This will run dynatrace MCP server as a pod in your cluster.
    | credentials are passed as env vars.

    .. code-block:: yaml

        apiVersion: v1
        kind: Pod
        metadata:
          name: dynatrace-mcp
          labels:
            app: dynatrace-mcp
        spec:
          containers:
            - name: supergateway
              image: supercorp/supergateway
              env:
                - name: DT_ENVIRONMENT
                  value: https://abcd1234.apps.dynatrace.com
                - name: OAUTH_CLIENT_ID
                  value: dt0s02.SAMPLE
                - name: OAUTH_CLIENT_SECRET
                  valueFrom:
                    secretKeyRef:
                      name: dynatrace-credentials
                      key: client_secret                   
              ports:
                - containerPort: 8003
              args:
                - "--stdio"
                - "npx -y @dynatrace-oss/dynatrace-mcp-server@latest /"
                - "--port"
                - "8003"
                - "--logLevel"
                - "debug"
              stdin: true
              tty: true
        ---
        apiVersion: v1
        kind: Service
        metadata:
          name: dynatrace-mcp
        spec:
          selector:
            app: dynatrace-mcp
          ports:
            - protocol: TCP
              port: 8003
              targetPort: 8003
          type: ClusterIP


2. Add MCP server to holmes config.
""""""""""""""""""""""""""""""""""""""

With the MCP server running in SSE mode, we need to let HolmesGPT know of the mcp server.
Use this config according to your use case.

**Configuration:**

.. md-tab-set::

  .. md-tab-item:: Holmes CLI

    Use a config file, and pass it when running cli commands.

    **custom_toolset.yaml:**

    .. code-block:: yaml

      mcp_servers:          
        mcp_server_1:
          description: "Dynatrace observability platform. Bring real-time observability data directly into your development workflow."
          url: "http://localhost:8003/sse"

    You can now use Holmes via the CLI with your configured MCP server. For example:

    .. code-block:: bash

      holmes ask -t custom_toolset.yaml  "Using dynatrace what issues do I have in my cluster?"  

  .. md-tab-item:: Robusta Helm Chart

    **Helm Values:**

    .. code-block:: yaml

      holmes:
        mcp_servers:          
          mcp_server_1:
            description: "Dynatrace observability platform. Bring real-time observability data directly into your development workflow."
            url: "http://dynatrace-mcp.default.svc.cluster.local:8003"

        
    Update your Helm values with the provided YAML configuration, then apply the changes with Helm upgrade:

    .. code-block:: bash

        helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

    After the deployment is complete, you can open the HolmesGPT chat in the Robusta SaaS UI and ask questions like *Using dynatrace what issues do I have in my cluster?*.
