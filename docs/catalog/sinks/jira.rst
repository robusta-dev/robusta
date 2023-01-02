Jira
#################

Robusta can send playbook results to Jira.

To configure the Jira sink we will need some parameters to be set.

.. note::

    2-way interactivity (``CallbackBlock``) isn't implemented yet.

Get your Jira configurations
------------------------------------------------

To configure the Jira sink you need to have following values: ``url``, ``username``, ``api_key``,  ``dedups`` ``and project_name``.

The ``url`` parameter is pretty simple to find: you need to copy the url of your workspace, usually
it looks like https://workspace.atlassian.net (**Note:** schema (https) is required)

The ``username`` it's the username you are logging with to Jira workspace.

``api_key`` can be configured, following the `instruction <https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/>`_.

``dedups`` is the parameter which defines how your tickets will be distinguished. The default value is the fingerprint,
so the issues with the same fingerprint won't be created. There can be more than one value to use. Possible values are:
fingerprint, cluster_name, title, node, type, source, namespace, creation_date etc

``project_name`` is the full name or shortened of the project so it can be found.

.. note::

   Permissions required for the user: ``write:jira-work``, ``read:jira-work``

Configuring the Jira sink
------------------------------------------------
Now we're ready to configure the Jira sink.

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

Save the file and run

.. code-block:: bash
   :name: cb-add-jira-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

You should now get playbooks results in Jira! Example is shown below:

    .. image:: /images/jira_example.png
      :width: 1000
      :align: center
