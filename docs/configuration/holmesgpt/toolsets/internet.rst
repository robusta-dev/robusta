Internet :checkmark:`_`
=======================
.. include:: ./_toolset_enabled_by_default.inc.rst

By enabling this toolset, HolmesGPT will be able to fetch webpages. This tool is beneficial if
you provide Holmes with publicly accessible web based runbooks.

Configuration
-------------

.. code-block:: yaml

    holmes:
        toolsets:
            internet:
                enabled: true
                config: # optional
                  additional_headers:
                    Authorization: Bearer ...

.. include:: ./_toolset_configuration.inc.rst

Capabilities
------------
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - fetch_webpage
     - Fetch a webpage. Use this to fetch runbooks if they are present before starting your investigation (if no other tool like confluence is more appropriate)
