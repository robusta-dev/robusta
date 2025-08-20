Namespace Resources API
==============================================

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

Use this endpoint to retrieve an **active count of specific Kubernetes resources** within a namespace. This is the same data displayed in the **Namespaces** tab of the Robusta UI.

You can specify exactly which resource kinds you want to query in the request.

.. _namespaces-resources-api:

POST https://api.robusta.dev/api/namespaces/resources
------------------------------------------------------

Prerequisites
^^^^^^^^^^^^^

This API relies on resource types configured in the Robusta UI sink.  
Make sure to configure all the individual resources you need as described in :ref:`cb-robusta-ui-sink-namespace-config`.

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
   * - ``namespace``
     - string
     - The name of the namespace you want to inspect.
     - Yes
   * - ``account_id``
     - string
     - The unique account identifier.
     - Yes
   * - ``cluster_name``
     - string
     - The name of the cluster where the namespace resides.
     - Yes
   * - ``resources``
     - list
     - A list of resource types to count, each including ``kind``, ``apiGroup``, and ``apiVersion``.
     - Yes

Resource Schema
^^^^^^^^^^^^^^^

Each item in the ``resources`` list must include:

* ``kind`` (e.g., `Deployments`)
* ``apiGroup`` (e.g., `apps`, or empty string for core group)
* ``apiVersion`` (e.g., `v1`, `v2`)

Example Request
^^^^^^^^^^^^^^^^^^^^

Here is an example of a ``POST`` request to query the resource count in a namespace:

.. code-block:: bash

    curl --location 'https://api.robusta.dev/api/namespaces/resources' \
    --header 'Authorization: Bearer API-KEY-HERE' \
    --header 'Content-Type: application/json' \
    --data '{
      "namespace": "your-namespace",
      "account_id": "your-account-id",
      "cluster_name": "your-cluster-name",
      "resources": [
        {"kind": "Deployments", "apiGroup": "apps", "apiVersion": "v1"},
        {"kind": "Services", "apiGroup": "", "apiVersion": "v1"},
        {"kind": "Ingresses", "apiGroup": "networking.k8s.io", "apiVersion": "v1"},
        {"kind": "CronJobs", "apiGroup": "batch", "apiVersion": "v1"}
      ]
    }'

Replace:

- ``API-KEY-HERE`` with your API Key from **Settings → API Keys → New API Key**.  
  Make sure the key has **Clusters → Read** permissions to access namespace resource data.
- ``your-account-id`` with the ID found in ``generated_values.yaml``
- ``your-cluster-name`` and ``your-namespace`` accordingly

Response Format
^^^^^^^^^^^^^^^^^^^^

Success Response
""""""""""""""""

If the request is successful, the API returns the following structure:

.. code-block:: json

    {
        "cluster": "your-cluster-name",
        "namespace": "your-namespace",
        "resources": [
            {
                "apiGroup": "apps",
                "apiVersion": "v1",
                "count": 2,
                "kind": "Deployments"
            },
            {
                "apiGroup": "",
                "apiVersion": "v1",
                "count": 3,
                "kind": "Services"
            },
            {
                "apiGroup": "networking.k8s.io",
                "apiVersion": "v1",
                "count": 1,
                "kind": "Ingresses"
            },
            ...
        ]
    }

- **Status Code**: `200 OK`

Error Response
""""""""""""""

If an error occurs, you will receive a response in the following format:

.. code-block:: json

    {
        "msg": "Error message here",
        "error_code": 456
    }

- **Status Code**: Varies depending on the error (e.g., `400`, `403`, `500`)