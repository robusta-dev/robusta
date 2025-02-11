Slab
====

Fetches slab pages

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
    holmes:
        additionalEnvVars:
            - name: SLAB_API_KEY
              value: <your slab API key>
        toolsets:
            slab:
                enabled: true


.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - fetch_slab_document
     - Fetch a document from slab. Use this to fetch runbooks if they are present before starting your investigation.
