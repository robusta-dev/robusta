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
              labels:
                pod: "kubernetes.pod_name"
                namespace: "kubernetes.namespace_name"
                app: "kubernetes.labels.app"

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
            labels:
              pod: "kubernetes.pod_name"
              namespace: "kubernetes.namespace_name"
              app: "kubernetes.labels.app"

        kubernetes/logs:
          enabled: false # Disable HolmesGPT's default logging mechanism


**Search labels**

You can tweak the labels used by the toolset to identify kubernetes resources. This is only needed if your
logs settings for ``pod``, ``namespace``, and ``app`` differ from the defaults in the example above.

You can verify what labels to use by attempting to run a query in the coralogix ui:

.. image:: /images/coralogix-logs-for-holmes-labels.png
  :width: 600
  :align: center


**Disabling the default toolset**

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
   * - coralogix_fetch_logs
     - Retrieve logs from Coralogix
