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

Cross-cluster tool calls from an external MCP client are opt-in per account. Turn on **Robusta MCP Server Enabled** under **Settings → AI Assistant → MCP Server Settings** before an API key can list or call any ``remote_*`` tool. It is off by default.

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

An API key is treated as an external caller and can only reach the cross-cluster ``remote_*`` tools (for example, listing available clusters and dispatching a tool call to one of them). It cannot call the static Slack, Teams, or incident-triage tools — those are reserved for Holmes' own internal use of this endpoint.

Calls run with the RBAC of the user who created the API key, not as an account-wide superuser: a key only reaches the clusters and namespaces its owner can already access. Deleting or demoting that user's access also narrows what the key can do.

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
