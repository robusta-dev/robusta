Datetime :checkmark:`_`
=======================
.. include:: ./_toolset_enabled_by_default.inc.rst

By enabling this toolset, HolmesGPT will be able to get the current UTC date and time.
This feature should be kept enabled as it can be necessary for other toolsets that rely
on dates and time.

The following built-in toolsets depend on ``datetime``:

* :ref:`grafana/loki <toolset_grafana_loki>`
* :ref:`prometheus/metrics <toolset_prometheus>`

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
