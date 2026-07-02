Send Events API
================

Send alerts from your monitoring system to Robusta through a single webhook endpoint.

This is the recommended ingestion path for new integrations. The legacy :doc:`Send Alerts API </configuration/exporting/send-alerts-api>` remains available for existing customers.

.. toctree::
   :maxdepth: 1
   :hidden:

   send-events/alertmanager
   send-events/aws-cloudwatch
   send-events/azure-monitor
   send-events/datadog
   send-events/dynatrace
   send-events/gcp-monitoring
   send-events/grafana
   send-events/nagios
   send-events/newrelic
   send-events/opsgenie
   send-events/pagerduty
   send-events/rootly
   send-events/sentry
   send-events/solarwinds
   send-events/splunk

Endpoint
--------

.. robusta-code::

    POST https://api.robusta.dev/webhooks?type=alert&origin=<ORIGIN>&account_id=<ACCOUNT_ID>

Query Parameters
----------------

.. list-table::
   :widths: 20 70
   :header-rows: 1

   * - Parameter
     - Description
   * - ``type``
     - Must be ``alert``.
   * - ``origin``
     - Identifies the monitoring product. Must be one of the supported origins listed under `Integrations`_ below.
   * - ``account_id``
     - Your Robusta account ID, found in ``generated_values.yaml``.
   * - ``cluster``
     - Optional. The cluster to associate the alert with. When set, it overrides any cluster found in the alert payload and is used for the resulting alert investigation. When omitted, the cluster is taken from the payload if present, otherwise the alert is recorded under the ``external`` cluster. Use this when your monitoring system cannot add a cluster label to the alert itself.

Authentication
--------------

Send your Robusta API key as a Bearer token. Generate keys in the Robusta UI under **Settings → API Keys → New API Key**.

.. code-block::

    Authorization: Bearer <API_KEY>

The key must be scoped to the ``account_id`` query parameter. Mismatches return ``401``.

Example Request
---------------

.. robusta-code:: bash

    curl --location --request POST \
      'https://api.robusta.dev/webhooks?type=alert&origin=datadog&account_id=ACCOUNT_ID' \
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

    .. grid-item-card:: :octicon:`server;1em;` GCP Cloud Monitoring
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/gcp-monitoring
        :link-type: doc

    .. grid-item-card:: :octicon:`server;1em;` Azure Monitor
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/azure-monitor
        :link-type: doc

    .. grid-item-card:: :octicon:`server;1em;` AWS CloudWatch
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/aws-cloudwatch
        :link-type: doc

Incident Management
~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` PagerDuty
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/pagerduty
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` Opsgenie
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/opsgenie
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` Rootly
        :class-card: sd-bg-light sd-bg-text-light
        :link: send-events/rootly
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
