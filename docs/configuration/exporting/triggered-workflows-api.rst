Triggered Workflows API
=======================

.. note::
    This API is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

Use this API to keep your Triggered Workflows in git and have a CI job create, update and delete them on the Robusta platform.

The API has one endpoint with two methods:

* **GET** returns every Triggered Workflow of the account.
* **POST** syncs a list of workflows to the account. It creates the ones that are new, updates the ones that exist, and with ``prune=true`` deletes the ones that are not in the list.

The output of ``GET`` is a valid ``POST`` body as it is. You can save it to a file, edit it and post it back.

.. _triggered-workflows-api:

Prerequisites
-------------

1. **An API key with the Triggered Workflows permission**

   Create one under **Settings** → **API Keys** → **New API Key**:

   * **Triggered Workflows: Read** is required for ``GET``
   * **Triggered Workflows: Write** is required for ``POST``

   Only an account admin can create an API key. Workflows the API creates are owned by the user who created the key.

2. **Your account ID**

   Find it in the Robusta UI under **Settings** → **General**.

.. warning::
    The key manages **every** Triggered Workflow of the account, including workflows made in the UI and private ones. Treat it like an admin credential.

Authentication
--------------

Send the API key as a Bearer token:

.. code-block:: text

    Authorization: Bearer YOUR_API_KEY

Endpoint
--------

.. robusta-code::

    GET  https://api.robusta.dev/api/triggered-workflows?account_id=YOUR_ACCOUNT_ID
    POST https://api.robusta.dev/api/triggered-workflows?account_id=YOUR_ACCOUNT_ID[&prune=true]

.. list-table::
   :widths: 20 10 60 10
   :header-rows: 1

   * - Parameter
     - Type
     - Description
     - Required
   * - ``account_id``
     - uuid
     - Your account ID. The API key must belong to this account.
     - Yes
   * - ``prune``
     - boolean
     - ``POST`` only. When ``true``, every workflow of the account that is not in the body is deleted. See :ref:`Pruning <triggered-workflows-api-prune>`. Default ``false``.
     - No

Choose your region (US, EU or AP) in any example box on this page to switch every URL to it. On a self-hosted platform, replace ``https://api.robusta.dev`` with your relay URL.

Workflow Fields
---------------

The body of ``POST`` and the response of ``GET`` are both ``{"workflows": [ ... ]}``, a list of entries with these fields:

.. list-table::
   :widths: 25 10 55 10
   :header-rows: 1

   * - Field
     - Type
     - Description
     - Required
   * - ``id``
     - uuid
     - The workflow's ID. You choose it (for example with ``uuidgen``), and it stays the same for the life of the workflow. Posting the same ``id`` again updates that workflow instead of creating a copy.
     - Yes
   * - ``title``
     - string
     - The workflow's name in the UI.
     - Yes
   * - ``prompt``
     - string
     - What Holmes should do with each event the workflow receives.
     - Yes
   * - ``additional_system_prompt``
     - string
     - Extra instructions added to Holmes's system prompt for this workflow.
     - No
   * - ``cluster_name``
     - string
     - The cluster Holmes investigates in.
     - Yes
   * - ``llm``
     - string
     - The model Holmes uses, as listed by the :doc:`LLM Models API <llm-models-api>`. When absent, the account's default model is used.
     - No
   * - ``enabled``
     - boolean
     - Whether the workflow runs. A disabled workflow skips the events it receives. Default ``true``.
     - No
   * - ``filters``
     - list
     - Up to 32 ``{"key": ..., "value_regex": ...}`` objects. The workflow runs only when **every** filter matches. A filter matches when a field named ``key``, anywhere in the event's JSON payload, has a value that ``value_regex`` matches (a regex search, so use ``^`` and ``$`` to match the whole value). When absent, the workflow runs on every event.
     - No
   * - ``create_incident``
     - boolean
     - Create incidents from this workflow's investigations. Default ``false``.
     - No
   * - ``daily_limit``
     - integer
     - The most Holmes investigations the workflow starts in any 24 hours. Events beyond it are skipped. Must be greater than 0. When absent, there is no limit (the UI suggests 20 when you create a workflow there).
     - No

Any other field, such as a typo or ``access_mode``, is rejected with a ``400``.

In a ``GET`` response every field is present, with ``null`` for an optional field that is not set.

**Example:**

.. code-block:: json

    {
        "workflows": [
            {
                "id": "6f1c9a2e-3b7d-4e8f-9a0b-1c2d3e4f5a6b",
                "title": "Pod crash loop triage",
                "prompt": "Investigate the crashing pod in the alert. Find the root cause and suggest a fix.",
                "additional_system_prompt": null,
                "cluster_name": "prod-us-east-1",
                "llm": null,
                "enabled": true,
                "filters": [
                    {"key": "alertname", "value_regex": "^KubePodCrashLooping$"},
                    {"key": "severity", "value_regex": "^(critical|high)$"}
                ],
                "create_incident": true,
                "daily_limit": 50
            }
        ]
    }

List Workflows (GET)
--------------------

Returns every Triggered Workflow of the account, deleted ones excluded, ordered by ``id``.

**Request:**

.. robusta-code:: bash

    curl --fail-with-body -sS \
      'https://api.robusta.dev/api/triggered-workflows?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY'

To save the response to a file you can edit and post back, add ``-o workflows.json``.

**Response (200 OK):** ``{"workflows": [ ... ]}``, as in the example above.

The response never leaves a workflow out. If a workflow stored in the account cannot be written as a ``POST`` entry (for example it has no title or cluster, or a filter that does not compile), ``GET`` answers ``409`` and names every such workflow and field. Fix or delete those workflows in the UI and call ``GET`` again. A list with workflows missing would make a later ``POST ?prune=true`` delete them.

.. code-block:: json

    {
        "msg": "1 of 12 workflows cannot be expressed as a POST entry; fix or delete them in the UI first",
        "error_code": 4000,
        "errors": [
            {"id": "9a0b1c2d-3e4f-4a5b-8c6d-7e8f9a0b1c2d", "field": "cluster_name", "msg": "Field required"}
        ]
    }

Sync Workflows (POST)
---------------------

Sends the full list of workflows. For each entry:

* a new ``id`` creates the workflow;
* an existing ``id`` updates it, replacing every field with the entry's value. A field left out of the entry is cleared or reset to its default;
* the ``id`` of a deleted workflow restores it (see :ref:`Pruning <triggered-workflows-api-prune>`).

The whole sync runs in one transaction: either every change is applied or none is. A retry of a successful sync changes nothing more.

**Request:**

Save the workflows in a JSON file, for example ``workflows.json``, in the shape shown under `Workflow Fields`_. Then, from the folder that holds the file, run:

.. robusta-code:: bash

    curl --fail-with-body -sS -X POST \
      'https://api.robusta.dev/api/triggered-workflows?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY' \
      -H 'Content-Type: application/json' \
      --data @workflows.json

``--data @workflows.json`` tells curl to send the contents of ``workflows.json`` as the request body. The path is relative to the folder you run ``curl`` from; for a file elsewhere, write its path after the ``@``, such as ``--data @robusta/workflows.json``.

To keep the workflows in YAML instead, convert the file on the fly: ``--data @-`` makes curl read the body from its input.

.. robusta-code:: bash

    yq -o=json '.' workflows.yaml | curl --fail-with-body -sS -X POST \
      'https://api.robusta.dev/api/triggered-workflows?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY' \
      -H 'Content-Type: application/json' \
      --data @-

**Response (200 OK):**

.. code-block:: json

    {
        "created": ["c3a8e0f2-51d4-4b9a-a7e1-6d2f8b4c9e13"],
        "updated": ["6f1c9a2e-3b7d-4e8f-9a0b-1c2d3e4f5a6b"],
        "deleted": [],
        "warnings": [
            "workflow c3a8e0f2-51d4-4b9a-a7e1-6d2f8b4c9e13: cluster 'staging' is not connected to this account"
        ]
    }

* ``created``, ``updated``, ``deleted``: the IDs of the workflows the sync created (or restored), updated and deleted.
* ``warnings``: one line per workflow whose ``cluster_name`` is not connected to the account right now. A warning never fails the sync, so you can sync a workflow before its cluster comes up, but check the name for typos.

Workflows the API creates can be seen and edited by every member of the account. The API never changes who can see an existing workflow: a private workflow made in the UI stays private when a sync updates it.

**Validation:** the whole body is checked before anything is written. If any entry is invalid, the response is ``400`` with every error of every entry, and nothing changes:

.. code-block:: json

    {
        "msg": "2 of 42 workflows are invalid",
        "error_code": 4000,
        "errors": [
            {"id": "6f1c9a2e-3b7d-4e8f-9a0b-1c2d3e4f5a6b", "field": "filters[1].value_regex", "msg": "regex does not compile: missing ), unterminated subpattern at position 0"},
            {"id": "9a0b1c2d-3e4f-4a5b-8c6d-7e8f9a0b1c2d", "field": "daily_limit", "msg": "Input should be greater than 0"}
        ]
    }

``id`` is the entry's ``id`` as sent, or ``workflows[<index>]`` when the entry has none.

The rules: every ``id`` is a valid, unique uuid; ``title``, ``prompt`` and ``cluster_name`` are not empty; each filter's ``key`` is not empty and its ``value_regex`` compiles; at most 32 filters; ``daily_limit`` is greater than 0; no unknown fields. A private workflow cannot create incidents, so setting ``create_incident: true`` on a private workflow made in the UI also answers ``400``.

The body can be up to 5 MiB.

.. _triggered-workflows-api-prune:

Pruning
^^^^^^^

Add ``prune=true`` to make the body the complete list of the account's workflows:

.. robusta-code:: bash

    curl --fail-with-body -sS -X POST \
      'https://api.robusta.dev/api/triggered-workflows?account_id=YOUR_ACCOUNT_ID&prune=true' \
      -H 'Authorization: Bearer YOUR_API_KEY' \
      -H 'Content-Type: application/json' \
      --data @workflows.json

.. warning::
    ``prune=true`` **deletes every workflow of the account that is not in the body**, including workflows made in the UI and private ones.

    * An empty list, ``{"workflows": []}``, deletes **all** of the account's workflows.
    * There is no dry run and no confirmation.
    * A deleted workflow stops running: events sent to its webhook URL are skipped.

    Before the first sync with ``prune=true``, export the account with ``GET`` and commit that file, so every existing workflow is in it.

A pruned workflow is deleted the same way as **Delete workflow** in the UI: its past runs and incidents are kept. Listing its ``id`` in a later ``POST`` restores it, returned in ``created``, and its webhook URL works again. So syncing the file from before a prune undoes the prune. This also restores workflows deleted in the UI.

Example: Workflows in Git
-------------------------

Keep the workflows in a YAML file in your repository:

.. code-block:: yaml

    # robusta/triggered-workflows.yaml
    workflows:
      - id: 6f1c9a2e-3b7d-4e8f-9a0b-1c2d3e4f5a6b
        title: Pod crash loop triage
        prompt: |
          Investigate the crashing pod in the alert.
          Find the root cause and suggest a fix.
        cluster_name: prod-us-east-1
        filters:
          - key: alertname
            value_regex: ^KubePodCrashLooping$
        create_incident: true
        daily_limit: 50

      - id: c3a8e0f2-51d4-4b9a-a7e1-6d2f8b4c9e13
        title: Failed deployment rollout
        prompt: Find why the rollout in the event failed and which change caused it.
        cluster_name: prod-us-east-1
        enabled: false

To start from the workflows you already have, export them and convert the result to YAML:

.. robusta-code:: bash

    curl --fail-with-body -sS \
      'https://api.robusta.dev/api/triggered-workflows?account_id=YOUR_ACCOUNT_ID' \
      -H 'Authorization: Bearer YOUR_API_KEY' \
      | yq -P '.' > robusta/triggered-workflows.yaml

This is also how to move a workflow you built and tested in the UI into git: export, then commit the file. Its ``id`` stays the same, so its webhook URL does not change.

Then sync the file on every merge to your main branch. A GitHub Actions example, where the job converts the YAML file to ``workflows.json`` and posts it:

.. robusta-code:: yaml

    # .github/workflows/robusta-triggered-workflows.yaml
    name: Sync Robusta Triggered Workflows
    on:
      push:
        branches: [main]
        paths: [robusta/triggered-workflows.yaml]

    jobs:
      sync:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - name: Sync
            env:
              ROBUSTA_API_KEY: ${{ secrets.ROBUSTA_API_KEY }}
              ROBUSTA_ACCOUNT_ID: ${{ vars.ROBUSTA_ACCOUNT_ID }}
            run: |
              yq -o=json '.' robusta/triggered-workflows.yaml > workflows.json
              curl --fail-with-body -sS -X POST \
                "https://api.robusta.dev/api/triggered-workflows?account_id=${ROBUSTA_ACCOUNT_ID}&prune=true" \
                -H "Authorization: Bearer ${ROBUSTA_API_KEY}" \
                -H "Content-Type: application/json" \
                --data @workflows.json

``--fail-with-body`` makes the job fail on an error and print the response, so a ``400`` shows every invalid entry in the job log. Remove ``&prune=true`` if the file should add and update workflows but never delete the ones made in the UI.

Errors
------

Every error response has this shape. Validation errors (``400``, and the ``409`` from ``GET``) also have an ``errors`` list.

.. code-block:: json

    {
        "msg": "Error message",
        "error_code": 4000
    }

.. list-table::
   :widths: 10 90
   :header-rows: 1

   * - Status
     - Meaning
   * - ``200``
     - Success.
   * - ``400``
     - ``account_id`` is missing or not a uuid, the body is not ``{"workflows": [...]}``, or an entry is invalid. Nothing was written.
   * - ``401``
     - The API key is missing, invalid, or does not belong to ``account_id``.
   * - ``403``
     - The API key does not have the Triggered Workflows permission (Read for ``GET``, Write for ``POST``), or an ``id`` in the body is already used by another account. Choose a new ``id`` for that workflow.
   * - ``409``
     - ``GET``: a stored workflow cannot be returned as an entry; the ``errors`` list names it. ``POST``: another sync for the account is running; retry.
   * - ``413``
     - The body is larger than 5 MiB.
   * - ``500``, ``503``
     - A server error. Retry: repeating a sync is safe.

See Also
--------

* :doc:`Send Events API <send-events-api>`: send events to a workflow's webhook URL
* :doc:`LLM Models API <llm-models-api>`: list the models you can use in ``llm``
* :doc:`RBAC Configuration API <rbac-api>`: manage RBAC from code the same way
