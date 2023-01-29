Jira
#################

Robusta can open Jira tickets based on playbooks results.

Get your Jira configurations
------------------------------------------------

To configure the Jira sink you need to have following:

* ``url`` : The url of your workspace. For example: https://workspace.atlassian.net (**Note:** schema (https) is required)
* ``username`` : Jira workspace user name. For example: jira-user@company.com
* ``api_key`` : follow the `instructions <https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/>`_ to get your api key.
* ``project_name`` : Project for the Jira tickets.
* ``issue_type`` : [Optional - default: ``Task``] Jira ticket type
* ``dedups`` : [Optional - default: ``fingerprint``] Tickets deduplication parameter. By default, Only one issue per ``fingerprint`` will be created. There can be more than one value to use. Possible values are: fingerprint, cluster_name, title, node, type, source, namespace, creation_date etc
* ``project_type_id_override`` : [Optional - default: None] If available, will override the ``project_name`` configuration
* ``issue_type_id_override`` : [Optional - default: None] If available, will override the ``issue_type`` configuration


.. note::

   * The configured user should have the following permissions: ``write:jira-work``, ``read:jira-work``
   * If creating issues by ``project_name`` or ``issue_type`` fails, try specifying the corresponding ids using ``project_type_id_override`` and ``issue_type_id_override``

Configuring the Jira sink
------------------------------------------------

| Now we're ready to configure the Jira sink.
| To avoid too many Jira tickets, it's recommended to use :ref:`Sink Matchers <Sink Matchers>` to limit the number of created tickets.
| In the example below, tickets will be created for the ``CPUThrottlingHigh`` and ``KubePodCrashLooping`` Prometheus alerts.

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinks_config:
          - jira_sink:
            name: personal_jira_sink
            url: https://workspace.atlassian.net
            username: username
            api_key: api_key
            dedups: (OPTIONAL)
              - fingerprint
            project_name: project_name
            match:
               identifier: "(CPUThrottlingHigh|KubePodCrashLooping)"

Save the file and run

.. code-block:: bash
   :name: cb-add-jira-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

You should now get playbooks results in Jira! Example is shown below:

    .. image:: /images/jira_example.png
      :width: 1000
      :align: center


.. note::

    2-way interactivity (``CallbackBlock``) isn't implemented yet.
