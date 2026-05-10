Send Events API
================

Send alerts, incidents, and changes from any monitoring system to Robusta through a single webhook endpoint. HolmesGPT investigates each event against your live cluster state, logs, metrics, and connected data sources, and attaches its findings to help accelerate triage.

This is the recommended ingestion path for new integrations. The legacy :doc:`Send Alerts API </configuration/exporting/send-alerts-api>` remains available for existing customers.

.. toctree::
   :maxdepth: 1
   :hidden:

   send-events/alertmanager
   send-events/pagerduty
   send-events/datadog
   send-events/newrelic
   send-events/dynatrace
   send-events/grafana
   send-events/gcp-monitoring
   send-events/azure-monitor
   send-events/splunk
   send-events/sentry
   send-events/launchdarkly
   send-events/argocd
   send-events/github
   send-events/opsgenie
   send-events/rootly
   send-events/incidentio
   send-events/nagios
   send-events/solarwinds
   send-events/aws-cloudwatch

Overview
--------

The endpoint accepts any JSON payload. The request is parameterized by query string:

.. code-block::

    POST https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=<ORIGIN>&type=<TYPE>&labels=<LABELS>

Robusta stores every payload verbatim, then asynchronously parses it into the Robusta UI timeline. If a per-origin parser is registered for ``origin``, it is used; otherwise a generic JSON parser handles the payload. Parse failures are visible in the **Delivery Log** UI page so you can self-debug.

Query Parameters
----------------

.. list-table::
   :widths: 20 10 60 10
   :header-rows: 1

   * - Parameter
     - Type
     - Description
     - Required
   * - ``account_id``
     - string
     - Your Robusta account ID, found in ``generated_values.yaml``.
     - Yes
   * - ``origin``
     - string
     - Identifies the monitoring product (for example ``alertmanager``, ``pagerduty``, ``datadog``). Free-form; selects the per-origin parser when one exists.
     - Yes
   * - ``type``
     - string
     - One of ``alert``, ``incident``, or ``change``.
     - Yes
   * - ``labels``
     - string
     - Comma-separated list of free-form tags. Forwarded to the parsed event for use in workflows, routing, and AI investigation policies.
     - No

Authentication
--------------

Send your Robusta API key as a Bearer token. Generate keys in the Robusta UI under **Settings → API Keys → New API Key**.

.. code-block::

    Authorization: Bearer <API_KEY>

The key must be scoped to the ``account_id`` query parameter. Mismatches return ``401``.

Example Request
---------------

.. code-block:: bash

    curl --location --request POST \
      'https://api.robusta.dev/webhooks?account_id=ACCOUNT_ID&origin=datadog&type=alert&labels=env=prod,team=payments' \
      --header 'Authorization: Bearer API_KEY' \
      --header 'Content-Type: application/json' \
      --data-raw '{ "title": "High error rate", "severity": "high" }'

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

Integrations
------------

Pick your monitoring system below for step-by-step instructions. Each page provides the URL to paste into your vendor's webhook configuration along with the API key.

Prometheus & AlertManager
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` AlertManager
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/alertmanager
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` Grafana
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/grafana
        :link-type: doc

APM & Observability
~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` Datadog
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/datadog
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` New Relic
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/newrelic
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` Dynatrace
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/dynatrace
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` Splunk
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/splunk
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` Sentry
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/sentry
        :link-type: doc

Cloud Provider Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`cloud;1em;` GCP Cloud Monitoring
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/gcp-monitoring
        :link-type: doc

    .. grid-item-card:: :octicon:`cloud;1em;` Azure Monitor
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/azure-monitor
        :link-type: doc

    .. grid-item-card:: :octicon:`cloud;1em;` AWS CloudWatch
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/aws-cloudwatch
        :link-type: doc

Incident Management
~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`bell;1em;` PagerDuty
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/pagerduty
        :link-type: doc

    .. grid-item-card:: :octicon:`bell;1em;` Opsgenie
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/opsgenie
        :link-type: doc

    .. grid-item-card:: :octicon:`bell;1em;` Rootly
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/rootly
        :link-type: doc

    .. grid-item-card:: :octicon:`bell;1em;` Incident.io
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/incidentio
        :link-type: doc

Changes & Deployments
~~~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`git-branch;1em;` Argo CD
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/argocd
        :link-type: doc

    .. grid-item-card:: :octicon:`mark-github;1em;` GitHub
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/github
        :link-type: doc

    .. grid-item-card:: :octicon:`flame;1em;` LaunchDarkly
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/launchdarkly
        :link-type: doc

Other
~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` Nagios
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/nagios
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` SolarWinds
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/solarwinds
        :link-type: doc

Unsupported sources
-------------------

Any monitoring system that can POST JSON to a URL works. Pick a free-form ``origin`` value, paste the URL into the vendor's webhook configuration, and Robusta's generic parser will handle the payload. The AI investigator reads the raw payload along with the structured event, so source-specific fields are preserved even without a dedicated parser.

Delivery Log
------------

Every received payload — parsed, pending, or failed — is visible in the Robusta UI under **Settings → Delivery Log**, scoped to your account and sorted by recency. Use it to confirm that a vendor is reaching Robusta, view the original request body, and inspect parser errors.
