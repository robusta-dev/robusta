LLM Models API
==============

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

Use this endpoint to list the Robusta-hosted LLM models available to your account, along with the account's default model. This is useful if you are building a tool that lets a user pick a model, or that needs to know which model Holmes will use by default.

.. _llm-models-api:

POST https://api.robusta.dev/api/llm/models
---------------------------------------------

Request Body
^^^^^^^^^^^^

.. list-table::
   :widths: 20 10 60 10
   :header-rows: 1

   * - Parameter
     - Type
     - Description
     - Required
   * - ``account_id``
     - string
     - The unique account identifier (found in the Robusta UI under **Settings** -> **General**).
     - Yes
   * - ``session_token``
     - string
     - Unused for API key authentication; pass an empty string.
     - Yes

Authentication
^^^^^^^^^^^^^^

Send your Robusta API key as a Bearer token:

.. code-block::

    Authorization: Bearer <API_KEY>

The key must have the "Robusta AI" resource with "Write" permission. You can generate this token in the platform by navigating to **Settings** -> **API Keys** -> **New API Key**, and creating a key with the "Robusta AI" resource and "Write" permission.

Example Request
^^^^^^^^^^^^^^^

.. robusta-code:: bash

    curl -X POST 'https://api.robusta.dev/api/llm/models' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer API-KEY' \
    --data '{
        "account_id": "ACCOUNT_ID",
        "session_token": ""
    }'

Example Response
^^^^^^^^^^^^^^^^

.. code-block:: json

    {
        "models": ["claude-sonnet-4-5", "gpt-5.4"],
        "models_holmes_args": {},
        "default_model": "claude-sonnet-4-5"
    }

Response Fields
^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 15 60
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``models``
     - array
     - Robusta-hosted model names available to the account.
   * - ``models_holmes_args``
     - object
     - Per-model arguments Holmes needs to invoke each listed model.
   * - ``default_model``
     - string
     - The account's fallback Robusta-hosted model — used when a requested model is unavailable. Not necessarily the account's overall default, which may be a model defined on a connected agent instead of a Robusta-hosted one.

Error Responses
^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 15 30 55
   :header-rows: 1

   * - Status
     - Error
     - Description
   * - 401
     - Unauthorized
     - Invalid or missing API key.
   * - 403
     - Forbidden
     - API key lacks required "Robusta AI: Write" permission.
   * - 503
     - Service Unavailable
     - LLM registry is not configured, or account model settings are unavailable.

Other Versions
^^^^^^^^^^^^^^

``/api/llm/models/v2`` and ``/api/llm/models/v3`` use the same authentication and request body, and return a more detailed per-model payload (a model-name-keyed object rather than a flat list, plus the account's model preferences on ``v3``). They power the Robusta Platform's own model-picker UI; most integrations should use ``/api/llm/models`` above.

See Also
--------

* :doc:`Holmes Chat API <../holmesgpt/holmes-chat-api>` — the ``model`` field on a chat request accepts any model name returned here.
