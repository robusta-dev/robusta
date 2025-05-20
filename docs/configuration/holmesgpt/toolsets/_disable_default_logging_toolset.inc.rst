
Disabling the default toolset
*****************************

The default HolmesGPT logging tool **must** be disabled if you use a different datasource for logs.
HolmesGPT may still use kubectl to fetch logs and never call your datasource if ``kubernetes/logs`` is not disabled. 
To disable the default logging toolset, add the following to your holmes configuration:

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    .. code-block:: yaml

      holmes:
        toolsets:
          kubernetes/logs:
            enabled: false


    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    Add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

      toolsets:
        kubernetes/logs:
          enabled: false