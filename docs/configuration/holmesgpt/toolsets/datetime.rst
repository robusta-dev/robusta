Datetime :checkmark:`_`
=======================
.. include:: ./_toolset_enabled_by_default.inc.rst

By enabling this toolset, HolmesGPT will be able to get the current UTC date and time.
This feature works well with other toolsets.

The following built-in toolsets depend on ``datetime``:

* :ref:`grafana/loki <toolset_grafana_loki>`

Configuration
-------------

.. code-block:: yaml
    holmes:
        toolsets:
            datetime:
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
   * - get_current_time
     - Return current time information. Useful to build queries that require a time information
