Send Events API
================

Send events from your monitoring, feature-flag, and deployment systems
to Robusta through a single webhook endpoint. Events come in two
flavors today:

* **Alerts** — events that warrant investigation (Prometheus,
  Datadog, PagerDuty, etc.). See :doc:`send-alerts-api`.
* **Changes** — configuration / deployment changes that correlate with
  alerts (LaunchDarkly, Argo CD, GitHub). See :doc:`send-changes-api`.

This is the recommended ingestion path for new integrations. The
legacy :doc:`/api/alerts </configuration/exporting/send-alerts-api>` and
:doc:`/api/config-changes </configuration/exporting/configuration-changes-api>`
endpoints remain available for existing customers.

.. toctree::
   :maxdepth: 1
   :hidden:

   send-alerts-api
   send-changes-api

Endpoint
--------

.. code-block::

    POST https://api.robusta.dev/webhooks?type=<TYPE>&origin=<ORIGIN>&account_id=<ACCOUNT_ID>

Query Parameters
----------------

.. list-table::
   :widths: 20 70
   :header-rows: 1

   * - Parameter
     - Description
   * - ``type``
     - One of ``alert`` or ``change``. ``alert`` is the most common;
       ``change`` is used by feature-flag/deployment integrations.
   * - ``origin``
     - Identifies the source system (``alertmanager``, ``datadog``,
       ``launchdarkly``, ``github``, …). Any non-empty string is accepted —
       unknown origins are still stored and parsed by the generic parser.
   * - ``account_id``
     - Your Robusta account ID, found in ``generated_values.yaml``.

Authentication
--------------

Send your Robusta API key as a Bearer token. Generate keys in the
Robusta UI under **Settings → API Keys → New API Key**.

.. code-block::

    Authorization: Bearer <API_KEY>

The key must be scoped to the ``account_id`` query parameter. Mismatches
return ``401``. Vendors that cannot send custom HTTP headers may pass the
key as ``&token=<API_KEY>`` instead — the relay accepts either.

Example: Send an Alert
----------------------

.. code-block:: bash

    curl --location --request POST \
      'https://api.robusta.dev/webhooks?type=alert&origin=datadog&account_id=ACCOUNT_ID' \
      --header 'Authorization: Bearer API_KEY' \
      --header 'Content-Type: application/json' \
      --data-raw '{ "title": "High error rate", "severity": "high" }'

Example: Send a Change
----------------------

.. code-block:: bash

    curl --location --request POST \
      'https://api.robusta.dev/webhooks?type=change&origin=launchdarkly&account_id=ACCOUNT_ID' \
      --header 'Authorization: Bearer API_KEY' \
      --header 'Content-Type: application/json' \
      --data-raw '{ "name": "beta-checkout", "titleVerb": "updated", "parent": {"name": "production"} }'

Response
--------

A successful request returns ``200`` with the ID of the stored event:

.. code-block:: json

    { "id": "8f1b...e21" }

Errors:

* ``400`` — missing or empty ``account_id``, ``origin``, or ``type``; invalid ``type`` value.
* ``401`` — invalid or out-of-scope API key.
* ``429`` — rate limit exceeded (300 requests per 5-minute window per account).
* ``503`` — transient storage failure; vendors should retry.

Pick Your Source
----------------

.. grid:: 1 1 2 2
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` Send Alerts API
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-alerts-api
        :link-type: doc

        Wire your monitoring system to ``type=alert``. Per-origin
        configuration for AlertManager, Datadog, PagerDuty, and 11 others.

    .. grid-item-card:: :octicon:`git-branch;1em;` Send Changes API
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-changes-api
        :link-type: doc

        Wire your feature-flag or deployment system to ``type=change``.
        Per-origin configuration for LaunchDarkly, Argo CD, and GitHub.
