Confluence
==========

By enabling this toolset, HolmesGPT will be able to fetch confluence pages. This is particularly useful if you store runbooks in
Confluence and want Holmes to run investigations using these runbooks.
This toolset requires an `Atlassian API Key <https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/>`_.


Configuration
-------------

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    **Helm Values:**

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

  .. md-tab-item:: Holmes CLI

    Set the following environment variables and the Confluence toolset will be automatically enabled:

    .. code-block:: shell

        export CONFLUENCE_USER="<confluence username>"
        export CONFLUENCE_API_KEY="<confluence API key>"
        export CONFLUENCE_BASE_URL="<confluence's base URL>"


    To test, run: 

    .. code-block:: yaml
      
        holmes ask "why is my application failing? Get revelant runbooks from Confluence"

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
