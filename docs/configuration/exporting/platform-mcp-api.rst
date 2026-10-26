Platform MCP API
=================

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

Robusta exposes a `Model Context Protocol (MCP) <https://modelcontextprotocol.io/>`_ server that lets any MCP client — Claude Code, Claude Desktop, or your own agent — run cross-cluster investigation tools against every cluster connected to your account.

.. _platform-mcp-api:

POST https://api.robusta.dev/api/platform-mcp
-----------------------------------------------

A standard MCP `Streamable HTTP <https://modelcontextprotocol.io/specification/2025-06-18/basic/transports#streamable-http>`_ endpoint. It accepts the usual MCP JSON-RPC methods (``initialize``, ``tools/list``, ``tools/call``) as a single request or a batch.

Enabling external access
^^^^^^^^^^^^^^^^^^^^^^^^^

Access from an external MCP client is opt-in per account. Turn on **Robusta MCP Server Enabled** under **Settings → MCP Server** before an API key can list or call any tool. It is off by default.

Under that switch, each toolset the server exposes has its own switch (all on by default once the server is enabled):

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Toolset
     - Tools
   * - **Ask Holmes**
     - ``ask_holmes``, ``get_holmes_answer`` — ask the Holmes agent of a cluster a question and get back its full investigation.
   * - **Cluster tools**
     - ``list_available_clusters`` and the ``remote_*`` tools — run one of Holmes' cluster-local tools (kubectl, Prometheus, pod logs) on a cluster and get its raw output.

Authentication
^^^^^^^^^^^^^^

Send your Robusta API key as a Bearer token, with your account ID as the first word:

.. code-block::

    Authorization: Bearer <ACCOUNT_ID> <API_KEY>

The key must have the **Robusta AI: Write** permission. You can generate this token in the platform by navigating to **Settings** -> **API Keys** -> **New API Key**, and creating a key with the "Robusta AI" resource and "Write" permission.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Header
     - Description
   * - ``Authorization``
     - ``Bearer <ACCOUNT_ID> <API_KEY>``. The account ID and key are both required; there is no separate account ID parameter.

Example Request
^^^^^^^^^^^^^^^

A real MCP client opens every session with the standard ``initialize`` / ``notifications/initialized`` handshake before calling any tool method. The endpoint itself is stateless — it does not issue or check a session ID between requests — but showing the full sequence here keeps this example valid input for any spec-compliant MCP client, not just this server.

.. robusta-code:: bash

    curl -X POST 'https://api.robusta.dev/api/platform-mcp' \
    --header 'Content-Type: application/json' \
    --header 'Accept: application/json, text/event-stream' \
    --header 'MCP-Protocol-Version: 2025-03-26' \
    --header 'Authorization: Bearer ACCOUNT_ID API-KEY' \
    --data '{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "example-client", "version": "1.0.0"}
        }
    }'

    curl -X POST 'https://api.robusta.dev/api/platform-mcp' \
    --header 'Content-Type: application/json' \
    --header 'Accept: application/json, text/event-stream' \
    --header 'MCP-Protocol-Version: 2025-03-26' \
    --header 'Authorization: Bearer ACCOUNT_ID API-KEY' \
    --data '{
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }'

    curl -X POST 'https://api.robusta.dev/api/platform-mcp' \
    --header 'Content-Type: application/json' \
    --header 'Accept: application/json, text/event-stream' \
    --header 'MCP-Protocol-Version: 2025-03-26' \
    --header 'Authorization: Bearer ACCOUNT_ID API-KEY' \
    --data '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }'

MCP client configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

For Claude Code:

.. robusta-code:: bash

    claude mcp add --transport http robusta-platform \
      "https://api.robusta.dev/api/platform-mcp" \
      --header "Authorization: Bearer ACCOUNT_ID API-KEY"

For Claude Desktop or any generic MCP client (``mcp.json``):

.. code-block:: json

    {
      "mcpServers": {
        "robusta-platform": {
          "type": "http",
          "url": "https://api.robusta.dev/api/platform-mcp",
          "headers": {
            "Authorization": "Bearer ACCOUNT_ID API-KEY"
          }
        }
      }
    }

What an API key can call
^^^^^^^^^^^^^^^^^^^^^^^^^

An API key is treated as an external caller and can only reach the toolsets above. It cannot call the Slack, Teams, or incident-triage tools — those are reserved for Holmes' own internal use of this endpoint.

Calls run with the RBAC of the user who created the API key, not as an account-wide superuser: a key only reaches the clusters and namespaces its owner can already access. Deleting or demoting that user's access also narrows what the key can do.

Asking Holmes a question
^^^^^^^^^^^^^^^^^^^^^^^^^

``ask_holmes`` starts a Holmes investigation on a cluster, the same way the :doc:`Holmes Chat API <../holmesgpt/holmes-chat-api>` does, and returns the answer in markdown. An investigation can take seconds or minutes, longer than most MCP clients wait for one tool call, so the call is split in two:

* ``ask_holmes`` waits up to ``wait_seconds`` (default 50, at most 280) for the answer. When the answer is ready in time, the result has ``status: "completed"`` and the ``answer``; otherwise it has ``status: "running"`` and a ``conversation_id``.
* ``get_holmes_answer`` waits on that ``conversation_id`` again, with the same ``wait_seconds``, and returns the same shape. Call it until the status is ``completed``. The investigation keeps running between calls, so a client that times out loses nothing.

.. list-table::
   :widths: 20 15 65
   :header-rows: 1

   * - Argument
     - Required
     - Description
   * - ``question``
     - Yes
     - The question, with every detail Holmes needs (namespace, workload or pod names, time window, what was observed).
   * - ``cluster``
     - When more than one cluster can be asked
     - The cluster whose Holmes answers. The error of a call without it names the clusters you can ask.
   * - ``wait_seconds``
     - No
     - How long the call waits for the answer. Keep it under your MCP client's tool timeout.

Both tools answer with ``{"conversation_id", "cluster", "status", "answer", "ui_link"}``; ``ui_link`` opens the conversation in the Robusta UI.

.. code-block:: json

    {
      "conversation_id": "78170c9f-2403-43ac-88ed-d6d39efd90ed",
      "cluster": "prod-eu",
      "ui_link": "https://platform.robusta.dev/my-account/holmes/chat/78170c9f-2403-43ac-88ed-d6d39efd90ed",
      "status": "completed",
      "answer": "3 of the 12 pods in `checkout` restarted in the last hour ..."
    }

Only clusters whose Holmes agent takes conversations from the platform (Holmes 0.24 or later, with the conversation worker enabled) can be asked, and only those the key's owner may chat with.

Rate limits and errors
^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 15 30 55
   :header-rows: 1

   * - Status
     - Error
     - Description
   * - 401
     - Unauthorized
     - Missing/malformed ``Authorization`` header, invalid API key, or the key lacks the "Robusta AI: Write" capability.
   * - 429
     - Too Many Requests
     - Rate limit exceeded. Each actual tool call (not ``initialize``/``tools/list``) consumes one request against the limit; the response includes a ``Retry-After`` header.
   * - 500
     - Internal Server Error
     - Unhandled error while processing the request.

See Also
--------

* :doc:`Holmes Chat API <../holmesgpt/holmes-chat-api>` — for a single-turn "ask Holmes a question" REST API instead of a full MCP tool session.
