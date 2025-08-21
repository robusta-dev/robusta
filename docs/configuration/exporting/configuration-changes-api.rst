Configuration Changes API
==============================================

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

Use this endpoint to send configuration changes to Robusta. You can send up to 1000 configuration changes in a single request.

.. _send-configuration-changes-api:

POST https://api.robusta.dev/api/config-changes
--------------------------------------------------------------------

Request Body Schema
^^^^^^^^^^^^^^^^^^^

The request body must include the following fields:

.. list-table::
   :widths: 25 10 70 10
   :header-rows: 1

   * - Field
     - Type
     - Description
     - Required
   * - ``account_id``
     - string
     - The unique account identifier.
     - Yes
   * - ``config_changes``
     - list
     - A list of configuration changes.
     - Yes

Configuration Change Schema
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each configuration change in the ``config_changes`` list must follow the specific schema, which includes the following fields:

.. list-table::
   :widths: 25 10 70 10
   :header-rows: 1

   * - Field
     - Type
     - Description
     - Required
   * - ``title``
     - string
     - A short description of the configuration change.
     - Yes
   * - ``old_config``
     - string
     - The previous configuration value.
     - Yes
   * - ``new_config``
     - string
     - The new configuration value.
     - Yes
   * - ``resource_name``
     - string
     - The name of the resource affected by the configuration change.
     - Yes
   * - ``description``
     - string
     - A detailed description of the configuration change (optional).
     - No
   * - ``source``
     - string
     - The source of the configuration change (default: ``external``).
     - No
   * - ``cluster``
     - string
     - The cluster where the configuration change occurred (default: ``external``).
     - No
   * - ``labels``
     - dict
     - Extra labels for the alert (optional).
     - No
   * - ``annotations``
     - dict
     - Extra annotations for the configuration change (optional).
     - No
   * - ``subject_name``
     - string
     - The name of the subject related to the configuration change (optional).
     - No
   * - ``subject_namespace``
     - string
     - The namespace of the subject related to the configuration change (optional).
     - No
   * - ``subject_node``
     - string
     - The node where the subject related to the configuration change is located (optional).
     - No
   * - ``subject_type``
     - string
     - The type of subject related to the configuration change (optional).
     - No
   * - ``service_key``
     - string
     - A key identifying the service related to the configuration change (optional).
     - No
   * - ``fingerprint``
     - string
     - A unique identifier for the configuration change (optional).
     - No

Example Request
^^^^^^^^^^^^^^^^^^^^

Here is an example of a ``POST`` request to send a list of configuration changes:

.. code-block:: bash

    curl --location --request POST 'https://api.robusta.dev/api/config-changes' \
    --header 'Authorization: Bearer API-KEY' \
    --header 'Content-Type: application/json' \
    --data-raw '{
        "account_id": "ACCOUNT_ID",
        "config_changes": [
            {
                "title": "Updated test-service deployment",
                "old_config": "apiVersion: apps/v1\nkind: Deployment\n....",
                "new_config": "apiVersion: apps/v1...",
                "resource_name": "test sercvice",
                "description": "Changed deployemnt",
                "source": "test-service",
                "cluster": "prod-cluster-1",
                "labels": {
                    "environment": "production"
                },
                "annotations": {
                    "env1": "true"
                },
                "subject_namespace": "prod",
                "subject_node": "gke-prod-cluster-1-node-1"
            }
        ]
    }'

In this request, replace the following placeholders:

- ``ACCOUNT_ID``: Your account ID, which can be found in your ``generated_values.yaml`` file.
- ``API-KEY``: Your API Key for authentication. You can generate this token by navigating to **Settings** -> **API Keys** -> **New API Key**.

Request Headers
^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Header
     - Description
   * - ``Authorization``
     - Bearer token for authentication (e.g., ``Bearer TOKEN_HERE``). The token must have the necessary permissions to submit configuration changes.
   * - ``Content-Type``
     - Must be set to ``application/json``.

Response Format
^^^^^^^^^^^^^^^^^^^^

Success Response
""""""""""""""""

If the request is successful, the API will return the following response:

.. code-block:: json

    {
        "success": true
    }

- **Status Code**: `200 OK`

Error Response
""""""""""""""

If there is an error in processing the request, the API will return the following format:

.. code-block:: json

    {
        "msg": "Error message here",
        "error_code": 123
    }

- **Status Code**: Varies based on the error (e.g., `400 Bad Request`, `500 Internal Server Error`).