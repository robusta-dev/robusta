Internet
====

Fetches webpages. This tool is beneficial if you provide Holmes with publicly accessible web based runbooks.

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
    holmes:

        toolsets:
            internet:
                enabled: true


.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - fetch_webpage
     - Fetch a webpage. Use this to fetch runbooks if they are present before starting your investigation (if no other tool like confluence is more appropriate)
