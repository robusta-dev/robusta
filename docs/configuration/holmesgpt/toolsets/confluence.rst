Confluence
==========

By enabling this toolset, HolmesGPT will be able to fetch confluence pages. This is particularly useful if you store runbooks in
Confluence and want Holmes to run investigations using these runbooks.
This toolset requires an `API key <https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/>`_.


Configuration
-------------

.. code-block:: yaml

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

.. include:: ./_toolset_configuration.inc.rst

Capabilities
------------
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - fetch_confluence_url
     - Fetch a page in confluence.  Use this to fetch confluence runbooks if they are present before starting your investigation.
