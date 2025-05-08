.. _toolset_coralogix_logs:

Coralogix logs
==============

By enabling this toolset, HolmesGPT will fetch node and pods logs from `Coralogix <https://coralogix.com/>`_.

You **should** enable this toolset to replace the default :ref:`kubernetes/logs <toolset_kubernetes_logs>`
toolset if all your kubernetes/pod logs are consolidated inside Coralogix. It will make it easier for HolmesGPT
to fetch incident logs, including the ability to precisely consult past logs.


.. include:: ./_toolsets_that_provide_logging.inc.rst

Prerequisites
^^^^^^^^^^^^^

1. A `Coralogix API key <https://coralogix.com/docs/developer-portal/apis/data-query/direct-archive-query-http-api/#api-key>`_ which is assigned the ``DataQuerying`` permission preset
2. A `Coralogix domain <https://coralogix.com/docs/user-guides/account-management/account-settings/coralogix-domain/>`_. For example ``eu2.coralogix.com``
3. Your team's `name or hostname <https://coralogix.com/docs/user-guides/account-management/organization-management/create-an-organization/#teams-in-coralogix>`_. For example ``your-company-name``


You can deduct the ``domain`` and ``team_hostname`` configuration fields by looking at the URL you use to access the Coralogix UI.

For example if you access coralogix at ``https://my-team.app.eu2.coralogix.com/``` then the ``team_hostname`` is ``my-team``and the coralogix ``domain`` is ``eu2.coralogix.com``.

Configuration
^^^^^^^^^^^^^

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chat

    .. code-block:: yaml

      holmes:
        toolsets:
          coralogix/logs:
            enabled: true
            config:
              api_key: <your coralogix API key>
              domain: eu2.coralogix.com # Your Coralogix domain
              team_hostname: my-team # Your team's hostname in coralogix, without the domain part

          kubernetes/logs:
            enabled: false # Disable HolmesGPT's default logging mechanism


    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    Add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

      toolsets:
        coralogix/logs:
          enabled: true
          config:
            api_key: <your coralogix API key>
            domain: eu2.coralogix.com # Your Coralogix domain
            team_hostname: my-team # Your team's hostname in coralogix

        kubernetes/logs:
          enabled: false # Disable HolmesGPT's default logging mechanism

Advanced Configuration
^^^^^^^^^^^^^^^^^^^^^^

Frequent logs and archive
****************************

By default, holmes fetched the logs from the `Frequent search <https://coralogix.com/docs/user-guides/account-management/tco-optimizer/logs/#frequent-search-data-high-priority>`_ 
tier and only fetch logs from the `Archive` tier if the frequent search returned no result.

This behaviour can be customised using the ``logs_retrieval_methodology`` configuration field:

.. code-block:: yaml

  toolsets:
    coralogix/logs:
      enabled: true
      config:
        # Possible values are:
        #  - FREQUENT_SEARCH_ONLY
        #  - ARCHIVE_ONLY
        #  - ARCHIVE_FALLBACK  <- default value
        #  - FREQUENT_SEARCH_FALLBACK
        #  - BOTH_FREQUENT_SEARCH_AND_ARCHIVE
        logs_retrieval_methodology: ARCHIVE_FALLBACK # default value
        ...

Here is a description of each possible log retrieval methodology:

- **FREQUENT_SEARCH_ONLY** Always fetch logs using a frequent search.
- **ARCHIVE_ONLY** Always fetch logs using the archive.
- **ARCHIVE_FALLBACK** Use a frequent search first. If there are no results, fallback to searching archived logs. **This is the default behaviour.**
- **FREQUENT_SEARCH_FALLBACK** Search logs in the archive first. If there are no results, fallback to searching the frequent logs.
- **BOTH_FREQUENT_SEARCH_AND_ARCHIVE** Always use both the frequent search and the archive to fetch logs. The result contains merged data which is deduplicated and sorted by timestamp.

Search labels
***************

You can tweak the labels used by the toolset to identify kubernetes resources. This is **optional** and only needed if your
logs settings for ``pod``, ``namespace``, ``application`` and ``subsystem`` differ from the defaults in the example below.

.. code-block:: yaml

  toolsets:
    coralogix/logs:
      enabled: true
      config:
        labels: # OPTIONAL: tweak the filters used by HolmesGPT if your coralogix configuration is non standard
          namespace: "kubernetes.namespace_name"
          pod: "kubernetes.pod_name"
          application: "coralogix.metadata.applicationName"
          subsystem: "coralogix.metadata.subsystemName"
        ...


You can verify what labels to use by attempting to run a query in the coralogix ui:

.. image:: /images/coralogix-logs-for-holmes-labels.png
  :width: 600
  :align: center


Disabling the default toolset
*********************************

If Coralogix is your primary datasource for logs, it is **advised** to disable the default HolmesGPT logging
tool by disabling the ``kubernetes/logs`` toolset. Without this. HolmesGPT may still use kubectl to
fetch logs instead of Coralogix.

.. code-block:: yaml

    holmes:
        toolsets:
            kubernetes/logs:
                enabled: false


Capabilities
^^^^^^^^^^^^

.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - fetch_coralogix_logs_for_resource
     - Retrieve logs using coralogix
