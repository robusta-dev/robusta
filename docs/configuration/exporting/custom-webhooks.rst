Custom Webhooks
===============

Send alerts to Robusta from any monitoring system that supports HTTP webhooks.

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

Overview
--------

Robusta can receive alerts from any monitoring system that can send HTTP webhooks. This makes it easy to integrate with systems like Nagios, SolarWinds, or custom monitoring solutions.

Webhook Endpoint
----------------

Send alerts to Robusta using the following endpoint:

.. code-block:: bash

    POST https://api.robusta.dev/api/alerts

Authentication
--------------

You'll need your API key and account ID:

1. **Account ID**: Found in your ``generated_values.yaml`` file
2. **API Key**: Generate this in the Robusta platform under **Settings** → **API Keys** → **New API Key**

For detailed API documentation including request format, authentication, and examples, see :doc:`Alert History Import and Export API <exporting-data>`.

Quick Example
-------------

Here's a simple example of sending a custom alert:

.. code-block:: bash

    curl --location --request POST 'https://api.robusta.dev/api/alerts' \
        --header 'Authorization: Bearer YOUR_API_KEY' \
        --header 'Content-Type: application/json' \
        --data-raw '{
            "account_id": "YOUR_ACCOUNT_ID",
            "alerts": [
                {
                    "title": "Test Service Down",
                    "description": "The Test Service is not responding.",
                    "source": "monitoring-system",
                    "priority": "high",
                    "aggregation_key": "test-service-issues"
                }
            ]
        }'

Next Steps
----------

For complete API documentation including all available fields and response formats, see :doc:`Alert History Import and Export API <exporting-data>`.