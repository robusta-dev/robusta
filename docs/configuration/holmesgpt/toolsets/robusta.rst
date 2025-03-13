Robusta :checkmark:`_`
======================
.. include:: ./_toolset_enabled_by_default.inc.rst

By enabling this toolset, HolmesGPT will be able to fetch alerts metadata. It allows HolmesGPT to fetch information
about specific issues when chatting using "Ask Holmes". This toolset is not necessary for Root Cause Analysis.

Configuration
-------------

.. code-block:: yaml

    holmes:
        toolsets:
            robusta:
                enabled: true

.. include:: ./_toolset_configuration.inc.rst

Capabilities
------------
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - fetch_finding_by_id
     - Fetches a robusta finding. Findings are events, like a Prometheus alert or a deployment update
