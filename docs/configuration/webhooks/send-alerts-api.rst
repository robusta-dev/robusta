Send Alerts API
================

Forward alerts from your monitoring system to Robusta via the webhook
endpoint. Pick your monitoring system below for step-by-step
configuration instructions.

Endpoint
--------

.. code-block::

    POST https://api.robusta.dev/webhooks?type=alert&origin=<ORIGIN>&account_id=<ACCOUNT_ID>

See :doc:`send-events-api` for query parameters, authentication, and
error codes.

.. toctree::
   :maxdepth: 1
   :hidden:

   alerts/alertmanager
   alerts/aws-cloudwatch
   alerts/azure-monitor
   alerts/datadog
   alerts/dynatrace
   alerts/gcp-monitoring
   alerts/grafana
   alerts/nagios
   alerts/newrelic
   alerts/opsgenie
   alerts/pagerduty
   alerts/sentry
   alerts/solarwinds
   alerts/splunk

Prometheus & AlertManager
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` AlertManager
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/alertmanager
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` Grafana
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/grafana
        :link-type: doc

APM & Observability
~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` Datadog
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/datadog
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` New Relic
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/newrelic
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` Dynatrace
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/dynatrace
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` Splunk
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/splunk
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` Sentry
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/sentry
        :link-type: doc

Cloud Provider Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`server;1em;` GCP Cloud Monitoring
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/gcp-monitoring
        :link-type: doc

    .. grid-item-card:: :octicon:`server;1em;` Azure Monitor
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/azure-monitor
        :link-type: doc

    .. grid-item-card:: :octicon:`server;1em;` AWS CloudWatch
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/aws-cloudwatch
        :link-type: doc

Incident Management
~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` PagerDuty
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/pagerduty
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` Opsgenie
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/opsgenie
        :link-type: doc

Other
~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`pulse;1em;` Nagios
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/nagios
        :link-type: doc

    .. grid-item-card:: :octicon:`pulse;1em;` SolarWinds
        :class-card: sd-bg-light sd-bg-text-light
        :link: alerts/solarwinds
        :link-type: doc
