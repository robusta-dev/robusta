Robusta API Reference
==============================================

.. note::
    These features are available with the Robusta SaaS platform and self-hosted commercial plans. They are not available in the open-source version.

The Robusta platform exposes HTTP APIs for exporting data, sending alerts, and managing resources.

.. toctree::
   :maxdepth: 1
   
   send-alerts-api
   configuration-changes-api
   alert-export-api
   alert-statistics-api
   namespace-resources-api

Getting Started
---------------

All APIs require authentication using an API key. Generate API keys in the Robusta UI:

**Settings** → **API Keys** → **New API Key**

Assign appropriate permissions to your API key based on the APIs you plan to use.

Related Resources
-----------------

* For webhook integration, see :doc:`Custom Webhooks <custom-webhooks>`
* Example implementation: `Prometheus report-generator <https://github.com/robusta-dev/prometheus-report-generator>`_