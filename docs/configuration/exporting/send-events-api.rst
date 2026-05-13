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
   send-events/sentry
   send-events/solarwinds
   send-events/splunk

Endpoint
--------

.. code-block::

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

Authentication
--------------

Send your Robusta API key as a Bearer token. Generate keys in the Robusta UI under **Settings → API Keys → New API Key**.

.. code-block::

    Authorization: Bearer <API_KEY>

Example Request
---------------

.. code-block:: bash

    curl --location --request POST \
      'https://api.robusta.dev/webhooks?type=alert&origin=datadog&account_id=ACCOUNT_ID' \
      --header 'Authorization: Bearer API_KEY' \
      --header 'Content-Type: application/json' \
      --data-raw '{ "title": "High error rate", "severity": "high" }'

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
