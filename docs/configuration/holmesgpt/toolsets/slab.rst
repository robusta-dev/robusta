Slab
====

By enabling this toolset, HolmesGPT will be able to consult runbooks from Slab pages.
Retrieve your Slab `API token <https://help.slab.com/en/articles/6545629-developer-tools-api-webhooks>`_ prior to configuring this toolset. Do note that Slab API is only available for Slab premium users. See `here <https://help.slab.com/en/articles/6545629-developer-tools-api-webhooks>`_.

Configuration
-------------

.. code-block:: yaml

    holmes:
        additionalEnvVars:
            - name: SLAB_API_KEY
              value: <your slab API key>
        toolsets:
            slab:
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
   * - fetch_slab_document
     - Fetch a document from slab. Use this to fetch runbooks if they are present before starting your investigation.
