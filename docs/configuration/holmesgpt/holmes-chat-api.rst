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
