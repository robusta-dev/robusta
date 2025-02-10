Confluence
====

Fetch confluence pages. This is particularly useful if you store runbooks in Confluence.

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
    holmes:
        additionalEnvVars:
            - name: CONFLUENCE_USER
              value: <Confluence's username>
            - name: CONFLUENCE_API_KEY
              value: <Confluence's API key>
            - name: CONFLUENCE_BASE_URL
              value: <Confluence's base URL>

        toolsets:
            confluence:
                enabled: true

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - fetch_confluence_url
     - Fetch a page in confluence.  Use this to fetch confluence runbooks if they are present before starting your investigation.
