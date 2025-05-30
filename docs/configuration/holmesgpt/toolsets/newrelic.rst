New Relic
=========

By enabling this toolset, HolmesGPT will be able to pull traces and logs from New Relic for analysis.

Configuration
-------------

.. code-block:: yaml

    holmes:
        toolsets:
            newrelic:
                enabled: true
                config:
                    nr_api_key: ******
                    nr_account_id: ******

Below is a description of the configuration fields:

.. list-table::
  :header-rows: 1
  :widths: 20 80

  * - Config key
    - Description
  * - nr_api_key
    - Your New Relic API key with necessary permissions to access traces and logs
  * - nr_account_id
    - Your New Relic account ID

For more details on New Relic's API and authentication methods, refer to the `New Relic API documentation <https://docs.newrelic.com/docs/apis>`_.

.. include:: ./_toolset_configuration.inc.rst

Capabilities
------------
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - newrelic_get_logs
     - Retrieve logs from New Relic for a specific application and time range
   * - newrelic_get_traces
     - Retrieve traces from New Relic based on duration threshold or specific trace ID 