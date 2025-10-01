RBAC Configuration API
======================

The RBAC (Role-Based Access Control) Configuration API allows you to programmatically manage permission groups and scopes for your Robusta account.

.. note::
    This API is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

Overview
--------

The RBAC API provides a single endpoint with three operations:

* **GET** - Retrieve current RBAC configuration
* **POST** - Set/update RBAC configuration
* **DELETE** - Remove all RBAC configurations

Prerequisites
-------------

Before using the RBAC API, you need:


   Create at: https://platform.robusta.dev/settings#api-keys

   * **RBAC: READ** — required for ``GET``
   * **RBAC: WRITE** — required for ``POST`` and ``DELETE``

2. **Account ID**

   Find at: https://platform.robusta.dev/settings#workspace

Authentication
--------------

All requests require API key authentication. Include your API key in the request headers:

.. code-block:: bash

    Authorization: Bearer YOUR_API_KEY

API Endpoint
------------

``/api/rbac?account_id=YOUR_ACCOUNT_ID``

All operations use the same endpoint with different HTTP methods.

Operations
----------

Get RBAC Configuration
^^^^^^^^^^^^^^^^^^^^^^

Retrieve the current RBAC configuration for your account.

**Request:**

.. code-block:: bash

    curl -X GET 'https://api.robusta.dev/api/rbac?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY'

**Response (200 OK):**

.. code-block:: json

    {
        "account_id": "YOUR_ACCOUNT_ID",
        "scopes": [
            {
                "name": "production-scope",
                "type": "namespace",
                "clusters": {
                    "production-cluster": ["default", "app-namespace"]
                }
            }
        ],
        "groups": [
            {
                "name": "developers",
                "provider_group_id": "dev-team-id",
                "type": "namespace",
                "scopes": ["production-scope"],
                "permissions": ["APP_VIEW", "POD_LOGS", "METRICS_VIEW"]
            }
        ],
        "role_permission_groups": [
            {
                "name": "admin-group",
                "provider_group_id": "admin-team-id",
                "type": "ADMIN"
            }
        ]
    }

Set RBAC Configuration
^^^^^^^^^^^^^^^^^^^^^^^

Create or update the RBAC configuration for your account.

.. warning::
    This operation **completely replaces** all existing RBAC configurations. The API will:

    * Delete ALL existing scopes, groups, and role_permission_groups
    * Create new configurations based on the provided request body

    If you omit any of these fields (scopes, groups, or role_permission_groups), those configurations will be deleted and not replaced. To preserve existing configurations, you must include them in your request.

**Request:**

.. code-block:: bash

    curl -X POST 'https://api.robusta.dev/api/rbac?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY' \
      -H 'Content-Type: application/json' \
      -d '{
        "account_id": "YOUR_ACCOUNT_ID",
        "scopes": [...],
        "groups": [...],
        "role_permission_groups": [...]
      }'

**Request Body Example:**

.. code-block:: json

    {
        "account_id": "YOUR_ACCOUNT_ID",
        "scopes": [
            {
                "name": "production-scope",
                "type": "namespace",
                "clusters": {
                    "production-cluster": ["default", "app-namespace"]
                }
            },
            {
                "name": "staging-scope",
                "type": "cluster",
                "clusters": {
                    "staging-cluster": ["*"]
                }
            }
        ],
        "groups": [
            {
                "name": "developers",
                "provider_group_id": "dev-team-id",
                "type": "namespace",
                "scopes": ["production-scope"],
                "permissions": ["APP_VIEW", "POD_LOGS", "METRICS_VIEW"]
            },
            {
                "name": "devops",
                "provider_group_id": "devops-team-id", 
                "type": "cluster",
                "scopes": ["staging-scope"],
                "permissions": ["NODE_VIEW", "CLUSTER_VIEW", "KRR_SCAN"]
            }
        ],
        "role_permission_groups": [
            {
                "name": "admin-group",
                "provider_group_id": "admin-team-id",
                "type": "ADMIN"
            }
        ]
    }

**Response (201 Created):**

.. code-block:: json

    {
        "msg": "RBAC definitions processed successfully",
        "account_id": "YOUR_ACCOUNT_ID",
        "scopes_count": 2,
        "groups_count": 2
    }

Delete RBAC Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

Remove all RBAC configurations for your account.

**Request:**

.. code-block:: bash

    curl -X DELETE 'https://api.robusta.dev/api/rbac?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY'

**Response (200 OK):**

.. code-block:: json

    {
        "msg": "RBAC role deleted successfully"
    }

Configuration Schema
--------------------

Scopes
^^^^^^

Scopes define the resources (clusters and namespaces) that permissions apply to.

.. code-block:: json

    {
        "name": "string",           // Unique name for the scope
        "type": "namespace|cluster", // Scope type
        "clusters": {                // Cluster-to-namespace mapping
            "cluster-name": ["namespace1", "namespace2"] // or ["*"] for all namespaces
        }
    }

**Scope Types:**

* ``namespace`` - Permissions apply to specific namespaces within clusters
* ``cluster`` - Permissions apply to entire clusters

Groups
^^^^^^

Groups define permission sets that can be assigned to users via SSO provider groups.

.. code-block:: json

    {
        "name": "string",                    // Group name
        "provider_group_id": "string",       // SSO provider group ID
        "type": "namespace|cluster",         // Permission scope type
        "scopes": ["scope-name"],            // List of scope names
        "permissions": ["PERMISSION_NAME"]   // List of permissions
    }

Role Permission Groups
^^^^^^^^^^^^^^^^^^^^^^

Role permission groups assign predefined roles to SSO provider groups.

.. code-block:: json

    {
        "name": "string",                // Group name
        "provider_group_id": "string",   // SSO provider group ID
        "type": "ADMIN|USER"             // Predefined role (note: field name is "type" not "role")
    }

**Available Roles:**

* ``ADMIN`` - Full administrative access
* ``USER`` - Standard user access

Available Permissions
---------------------

**Permissions for Namespace-Type Groups:**

These permissions are available for groups with ``type: "namespace"``:

* ``APP_VIEW`` - View applications
* ``APP_RESTART`` - Restart applications
* ``JOB_VIEW`` - View jobs
* ``JOB_DELETE`` - Delete jobs
* ``POD_LOGS`` - View pod logs
* ``POD_DELETE`` - Delete pods
* ``KRR_VIEW`` - View KRR recommendations
* ``POPEYE_VIEW`` - View Popeye scan results
* ``METRICS_VIEW`` - View metrics
* ``HOLMES_INVESTIGATE`` - Use Holmes AI investigation
* ``TIMELINE_VIEW`` - View event timeline

**Permissions for Cluster-Type Groups:**

Cluster-type groups (``type: "cluster"``) have access to all namespace permissions above, plus these cluster-specific permissions:

* ``NODE_VIEW`` - View nodes
* ``NODE_DRAIN`` - Drain nodes
* ``NODE_CORDON`` - Cordon nodes
* ``NODE_UNCORDON`` - Uncordon nodes
* ``CLUSTER_VIEW`` - View cluster information
* ``CLUSTER_DELETE`` - Delete clusters
* ``KRR_SCAN`` - Run KRR scans
* ``POPEYE_SCAN`` - Run Popeye scans
* ``ALERT_CONFIG_EDIT`` - Edit alert configurations
* ``ALERT_CONFIG_VIEW`` - View alert configurations
* ``SILENCES_VIEW`` - View alert silences
* ``SILENCES_EDIT`` - Edit alert silences
* ``HOLMES_CHAT`` - Use Holmes AI chat
* ``HOLMES_CUSTOMIZE`` - Customize Holmes AI

Error Responses
---------------

The API returns standard HTTP status codes:

* **200** - Success (GET, DELETE)
* **201** - Created (POST)
* **400** - Bad Request (e.g., account_id mismatch)
* **401** - Unauthorized (invalid or missing API key)
* **403** - Forbidden (insufficient permissions)
* **500** - Internal Server Error

Error Response Format:

.. code-block:: json

    {
        "msg": "Error message",
        "error_code": 0
    }

Examples
--------

**Set up namespace-level permissions for developers:**

.. code-block:: bash

    curl -X POST 'https://api.robusta.dev/api/rbac?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY' \
      -H 'Content-Type: application/json' \
      -d '{
        "account_id": "YOUR_ACCOUNT_ID",
        "scopes": [
            {
                "name": "dev-namespaces",
                "type": "namespace",
                "clusters": {
                    "production": ["dev", "staging"],
                    "development": ["*"]
                }
            }
        ],
        "groups": [
            {
                "name": "developers",
                "provider_group_id": "github-dev-team",
                "type": "namespace",
                "scopes": ["dev-namespaces"],
                "permissions": ["APP_VIEW", "APP_RESTART", "POD_LOGS", "METRICS_VIEW"]
            }
        ]
    }'

**Set up cluster-wide admin access:**

.. code-block:: bash

    curl -X POST 'https://api.robusta.dev/api/rbac?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY' \
      -H 'Content-Type: application/json' \
      -d '{
        "account_id": "YOUR_ACCOUNT_ID",
        "role_permission_groups": [
            {
                "name": "platform-admins",
                "provider_group_id": "github-admin-team",
                "type": "ADMIN"
            }
        ]
    }'

**Complex configuration with multiple scopes and permission groups:**

.. code-block:: bash

    curl -X POST 'https://api.robusta.dev/api/rbac?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY' \
      -H 'Content-Type: application/json' \
      -d '{
        "account_id": "YOUR_ACCOUNT_ID",
        "scopes": [
            {
                "name": "prod-apps",
                "type": "namespace",
                "clusters": {
                    "prod-cluster": ["app-1", "app-2", "app-3"]
                }
            },
            {
                "name": "staging-full",
                "type": "cluster",
                "clusters": {
                    "staging-cluster": ["*"]
                }
            }
        ],
        "groups": [
            {
                "name": "prod-developers",
                "provider_group_id": "github-prod-dev",
                "type": "namespace",
                "scopes": ["prod-apps"],
                "permissions": [
                    "APP_VIEW",
                    "APP_RESTART",
                    "POD_LOGS",
                    "METRICS_VIEW",
                    "TIMELINE_VIEW"
                ]
            },
            {
                "name": "devops-team",
                "provider_group_id": "github-devops",
                "type": "cluster",
                "scopes": ["staging-full"],
                "permissions": [
                    "NODE_VIEW",
                    "NODE_DRAIN",
                    "CLUSTER_VIEW",
                    "KRR_SCAN",
                    "ALERT_CONFIG_VIEW"
                ]
            }
        ],
        "role_permission_groups": [
            {
                "name": "sre-admins",
                "provider_group_id": "github-sre",
                "type": "ADMIN"
            }
        ]
    }'

**Retrieve current configuration:**

.. code-block:: bash

    curl -X GET 'https://api.robusta.dev/api/rbac?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY'

**Clear all RBAC configurations:**

.. code-block:: bash

    curl -X DELETE 'https://api.robusta.dev/api/rbac?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY'

Important Notes
---------------

1. **Cluster Scope Auto-Population**: When creating configurations, the API automatically populates cluster scopes based on your account's active clusters. Use ``"*"`` as the cluster name to apply to all clusters.

2. **Provider Group IDs**: The ``provider_group_id`` should match the group identifier from your SSO provider (e.g., GitHub team ID, Okta group ID).

3. **Scope References**: Groups reference scopes by name. Ensure scope names are defined before referencing them in groups.

4. **Account ID Validation**: The ``account_id`` in the request body must match the ``account_id`` in the query parameter.

5. **No Active Clusters**: The API will return an error if no active clusters are found for your account.

6. **Automatic Permission Inclusion**: The API automatically includes minimal permissions for each group type. Namespace groups receive basic view permissions, and cluster groups receive basic view and node permissions.

7. **Wildcard Permissions**: Using ``["*"]`` as permissions will grant all available permissions for that scope type.

8. **Cluster Scope Validation**: For cluster-type scopes, namespaces must be ``["*"]`` only. Specific namespace lists are not allowed for cluster scopes.

See Also
--------

* :doc:`send-alerts-api` - Send alerts to Robusta
* :doc:`alert-export-api` - Export alerts from Robusta