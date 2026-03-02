Holmes Chat API
===============

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

Use this endpoint to send questions to Holmes AI for root cause analysis. You can provide alert context and Holmes will investigate and return a detailed markdown analysis.

.. _holmes-chat-api:

POST https://api.robusta.dev/api/holmes/<account_id>/chat
---------------------------------------------------------

URL Parameters
^^^^^^^^^^^^^^

.. list-table::
   :widths: 20 10 70 10
   :header-rows: 1

   * - Parameter
     - Type
     - Description
     - Required
   * - ``account_id``
     - string
     - The unique account identifier (found in your ``generated_values.yaml`` file).
     - Yes

Request Body
^^^^^^^^^^^^

.. list-table::
   :widths: 20 10 60 10
   :header-rows: 1

   * - Parameter
     - Type
     - Description
     - Required
   * - ``cluster_id``
     - string
     - The cluster to query. If not provided, Holmes will try to extract it from the payload or use the single connected cluster.
     - No
   * - ``ask``
     - string
     - The question to ask Holmes.
     - Yes
   * - ``payload``
     - object
     - Alert payload or context data for Holmes to analyze (e.g., Prometheus alert labels).
     - No
   * - ``additional_system_prompt``
     - string
     - Additional instructions to include in the system prompt.
     - No
   * - ``model``
     - string
     - The AI model to use. If not provided, uses the account default.
     - No

Example Request
^^^^^^^^^^^^^^^

The following ``curl`` command demonstrates how to ask Holmes about a failing pod:

.. code-block:: bash

    curl -X POST 'https://api.robusta.dev/api/holmes/ACCOUNT_ID/chat' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer API-KEY' \
    --data '{
        "cluster_id": "my-cluster",
        "ask": "Which pods are failing in the cluster?",
        "payload": {
            "alertname": "KubeContainerWaiting",
            "container": "frontend",
            "namespace": "production",
            "pod": "frontend-59fbcd7965-drx6w",
            "reason": "ContainerCreating",
            "severity": "warning"
        }
    }'

In the command, make sure to replace the following placeholders:

- ``ACCOUNT_ID``: Your account ID, which can be found in your ``generated_values.yaml`` file.
- ``API-KEY``: Your API Key for authentication. You can generate this token in the platform by navigating to **Settings** -> **API Keys** -> **New API Key**, and creating a key with the "Robusta AI" resource and "Write" permission.

Request Headers
^^^^^^^^^^^^^^^

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Header
     - Description
   * - ``Content-Type``
     - Must be ``application/json``.
   * - ``Authorization``
     - Bearer token for authentication (e.g., ``Bearer TOKEN_HERE``). The token must have "Robusta AI" resource with "Write" permission.

Response Format
^^^^^^^^^^^^^^^

The API returns a JSON object containing the cluster ID and the analysis in markdown format.

Example Response
^^^^^^^^^^^^^^^^

.. code-block:: json

    {
        "cluster_id": "my-cluster",
        "analysis": "## Investigation Summary\n\n### Failing Pods\n\n| Pod | Namespace | Status | Reason |\n|-----|-----------|--------|--------|\n| `frontend-59fbcd7965-drx6w` | production | Pending | ContainerCreating |\n\n**Root Cause**: Missing Secret - The pod is stuck because the secret `frontend-api-keys` does not exist.\n\n### Fix\n\n```bash\nkubectl create secret generic frontend-api-keys --from-literal=API_KEY=<your-key> -n production\n```"
    }

Response Fields
^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 10 70
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``cluster_id``
     - string
     - The cluster that was queried.
   * - ``analysis``
     - string
     - Holmes AI analysis in markdown format. Contains investigation findings, root cause analysis, and remediation steps.

Handling the Markdown Response
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``analysis`` field contains markdown text with escaped newlines (``\n``). To render it properly:

**Python:**

.. code-block:: python

    import json

    response_data = json.loads(response.text)
    markdown_text = response_data["analysis"]  # Already unescaped by json.loads
    print(markdown_text)  # Renders with proper line breaks

**JavaScript:**

.. code-block:: javascript

    const data = JSON.parse(responseText);
    const markdownText = data.analysis;  // Already unescaped by JSON.parse
    // Use a markdown renderer like marked.js or react-markdown

**Bash (using jq):**

.. code-block:: bash

    curl ... | jq -r '.analysis'  # -r outputs raw string with actual newlines

Error Responses
^^^^^^^^^^^^^^^

.. list-table::
   :widths: 15 30 55
   :header-rows: 1

   * - Status
     - Error
     - Description
   * - 400
     - Bad Request
     - Invalid request body or could not determine cluster.
   * - 401
     - Unauthorized
     - Invalid or missing API key.
   * - 403
     - Forbidden
     - API key lacks required permissions.
   * - 404
     - Not Found
     - Specified cluster is not connected to this account.
   * - 500
     - Internal Server Error
     - Holmes request failed.

Cluster Resolution
^^^^^^^^^^^^^^^^^^

If ``cluster_id`` is not provided in the request, Holmes will attempt to determine the cluster using the following logic:

1. Extract from ``payload`` fields (``cluster_name``, ``cluster``, ``cluster_id``, ``source``, or from ``labels``/``annotations``).
2. Use AI to extract the cluster name from the payload content.
3. If only one cluster is connected to the account, use that cluster.

If none of these methods succeed and multiple clusters are connected, the API will return an error listing the available clusters.


Streaming (SSE) Mode
---------------------

The same endpoint supports streaming responses via `Server-Sent Events (SSE) <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events>`_.
Instead of waiting for the full analysis, you receive a real-time stream of events as Holmes investigates — including tool calls, intermediate AI messages, and the final answer.

To enable streaming, set ``stream`` to ``true`` in the request body. All other parameters remain the same.

Example Streaming Request
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    curl -N -X POST 'https://api.robusta.dev/api/holmes/ACCOUNT_ID/chat' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer API-KEY' \
    --data '{
        "cluster_id": "my-cluster",
        "ask": "Which pods are failing in the cluster?",
        "stream": true,
        "payload": {
            "alertname": "KubeContainerWaiting",
            "container": "frontend",
            "namespace": "production",
            "pod": "frontend-59fbcd7965-drx6w"
        }
    }'

.. note::
    The ``-N`` flag disables output buffering in curl, which is important for seeing events as they arrive.

Streaming Response Format
^^^^^^^^^^^^^^^^^^^^^^^^^

The response has ``Content-Type: text/event-stream`` and uses the standard SSE wire format. Each event consists of an ``event`` line specifying the type, a ``data`` line containing a JSON payload, and a blank line:

.. code-block:: text

    event: <event_type>
    data: <json_payload>

Events are delivered in order as the investigation progresses. A typical stream looks like this:

.. code-block:: text

    event: start_tool_calling
    data: {"tool_call_id": "call_1", "tool_name": "kubectl_find_resource", "description": "Looking up failing pods"}

    event: tool_calling_result
    data: {"tool_call_id": "call_1", "name": "kubectl_find_resource", "result": {"status": "success", "data": "..."}}

    event: ai_message
    data: {"content": "I found a pod stuck in ContainerCreating state. Let me investigate further."}

    event: start_tool_calling
    data: {"tool_call_id": "call_2", "tool_name": "kubectl_describe_resource", "description": "Describing pod frontend-59fbcd7965-drx6w"}

    event: tool_calling_result
    data: {"tool_call_id": "call_2", "name": "kubectl_describe_resource", "result": {"status": "success", "data": "..."}}

    event: token_count
    data: {"input_tokens": 1520, "output_tokens": 305}

    event: ai_answer_end
    data: {"analysis": "## Investigation Summary\n\nThe pod `frontend-59fbcd7965-drx6w` is stuck ..."}

SSE Event Types
^^^^^^^^^^^^^^^

.. list-table::
   :widths: 22 78
   :header-rows: 1

   * - Event Type
     - Description
   * - ``start_tool_calling``
     - Holmes has started executing a tool (e.g., a ``kubectl`` command). Useful for showing progress indicators.
   * - ``tool_calling_result``
     - A tool call has completed. Contains the result or error information.
   * - ``ai_message``
     - An intermediate text message from the AI while it is still investigating. These are partial thoughts, not the final answer.
   * - ``ai_answer_end``
     - The final analysis. The ``analysis`` field contains the same markdown text you would receive from the non-streaming endpoint. **This is a terminal event** — no more events follow.
   * - ``error``
     - An error occurred during the investigation. **This is a terminal event.**
   * - ``token_count``
     - Token usage statistics for the request.
   * - ``approval_required``
     - Holmes needs user approval before executing a potentially dangerous tool. See :ref:`approval-required-event` below.

Event Payloads
^^^^^^^^^^^^^^

``start_tool_calling``
""""""""""""""""""""""

Emitted when Holmes begins executing a tool.

.. code-block:: json

    {
        "tool_call_id": "call_abc123",
        "tool_name": "kubectl_find_resource",
        "description": "kubectl get pods -n production"
    }

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``tool_call_id``
     - string
     - Unique identifier for this tool call. Use it to correlate with the corresponding ``tool_calling_result``.
   * - ``tool_name``
     - string
     - Name of the tool being executed.
   * - ``description``
     - string
     - Human-readable description of what the tool is doing.

``tool_calling_result``
"""""""""""""""""""""""

Emitted when a tool call completes.

.. code-block:: json

    {
        "tool_call_id": "call_abc123",
        "name": "kubectl_find_resource",
        "result": {
            "status": "success",
            "data": "NAME                        READY   STATUS    RESTARTS   AGE\nfrontend-59fbcd7965-drx6w   0/1     ContainerCreating   0   12m"
        }
    }

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``tool_call_id``
     - string
     - Matches the ``tool_call_id`` from the corresponding ``start_tool_calling`` event.
   * - ``name``
     - string
     - Name of the tool that was called.
   * - ``result``
     - object
     - Result object with a ``status`` field (``"success"``, ``"error"``, ``"no_data"``, or ``"approval_required"``) and either a ``data`` field (on success) or an ``error`` field (on failure).
   * - ``result_type``
     - string
     - Optional. ``"txt"`` (default) or ``"png"`` for image results.

``ai_message``
""""""""""""""

Emitted when the AI produces intermediate text during its investigation.

.. code-block:: json

    {
        "content": "I found a pod stuck in ContainerCreating state. Let me check the events."
    }

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``content``
     - string
     - The text content of the AI's intermediate message.

``ai_answer_end``
"""""""""""""""""

Emitted once when the investigation is complete. This is a **terminal event** — the stream ends after this.

.. code-block:: json

    {
        "analysis": "## Investigation Summary\n\n**Root Cause**: Missing Secret ..."
    }

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``analysis``
     - string
     - The complete analysis in markdown format. Identical to the ``analysis`` field in the non-streaming response.

``error``
"""""""""

Emitted when an error occurs. This is a **terminal event** — the stream ends after this.

.. code-block:: json

    {
        "msg": "Failed to connect to cluster",
        "error_code": "CLUSTER_ERROR"
    }

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``msg``
     - string
     - Human-readable error message.
   * - ``error_code``
     - string
     - Optional error code identifier.

``token_count``
"""""""""""""""

Emitted with token usage statistics.

.. code-block:: json

    {
        "input_tokens": 1520,
        "output_tokens": 305
    }

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``input_tokens``
     - integer
     - Number of input tokens consumed.
   * - ``output_tokens``
     - integer
     - Number of output tokens generated.

.. _approval-required-event:

``approval_required``
"""""""""""""""""""""

Emitted when Holmes needs explicit user approval before executing a tool. This is a **terminal event** — the stream pauses until approval is granted.

.. code-block:: json

    {
        "conversation_history": [
            {
                "role": "assistant",
                "content": "I need to run a command that modifies resources.",
                "tool_calls": [
                    {
                        "id": "call_xyz789",
                        "pending_approval": true,
                        "function": {
                            "name": "kubectl_exec",
                            "arguments": "{\"command\": \"kubectl delete pod test-pod -n default\"}"
                        }
                    }
                ]
            }
        ]
    }

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``conversation_history``
     - array
     - The full conversation history including the pending tool call. Assistant messages contain a ``tool_calls`` array where entries with ``"pending_approval": true`` are the tools awaiting approval.

Consuming the Stream
^^^^^^^^^^^^^^^^^^^^

**Python (using requests):**

.. code-block:: python

    import requests
    import json

    response = requests.post(
        "https://api.robusta.dev/api/holmes/ACCOUNT_ID/chat",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer API-KEY",
        },
        json={
            "ask": "Which pods are failing on cluster prod-us?",
            "stream": True,
        },
        stream=True,
    )

    event_type = None
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("event: "):
            event_type = line[7:]
        elif line.startswith("data: ") and event_type:
            data = json.loads(line[6:])
            if event_type == "ai_answer_end":
                print("Final analysis:", data["analysis"])
            elif event_type == "ai_message":
                print("AI:", data["content"])
            elif event_type == "start_tool_calling":
                print(f"Running tool: {data['tool_name']}")
            elif event_type == "error":
                print(f"Error: {data['msg']}")
            event_type = None
