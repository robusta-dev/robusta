Slab
====

By enabling this toolset, HolmesGPT will be able to consult runbooks from Slab pages.
Retrieve your Slab `API token <https://help.slab.com/en/articles/6545629-developer-tools-api-webhooks>`_ prior to configuring this toolset. Do note that Slab API is only available for Slab premium users. See `here <https://help.slab.com/en/articles/6545629-developer-tools-api-webhooks>`_.

Configuration
-------------


.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    .. code-block:: yaml

        holmes:
            additionalEnvVars:
                - name: SLAB_API_KEY
                  value: <your slab API key>
            toolsets:
                slab:
                    enabled: true

    .. include:: ./_toolset_configuration.inc.rst

  
  .. md-tab-item:: Holmes CLI

    First create the following environment variable:

    .. code-block:: shell

      export SLAB_API_KEY="<your slab API key>"

      
    Then add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

          toolsets:
            slab:
              enabled: true

    To test, run: 

    .. code-block:: yaml
      
        holmes ask "Why is my pod failing, if its a crashloopbackoff use the runbooks from slab"


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
