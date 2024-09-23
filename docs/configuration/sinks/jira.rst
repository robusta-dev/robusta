Jira
#################

Robusta can automatically open and (optionally) resolve Jira tickets, based on issues in your Kubernetes cluster.

  .. image:: /images/jira_example.png
    :width: 1000
    :align: center

To configure the Jira destination you need to have following:

Prerequisites
---------------------------------
* ``url`` : The url of your workspace. For example: https://workspace.atlassian.net (**Note:** schema (https) is required)
* ``username`` : The email you use to log into your Jira account. Eg: jira-user@company.com
* ``api_key`` : Follow these `instructions <https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/>`_ to get your api key.
* ``project_name`` : Project you want the Jira tickets to be created in. Go to **Project Settings** -> **Details** -> **Name**.

.. note::

   * The configured user should have the following permissions: ``write:jira-work``, ``read:jira-work``

Optional Settings
---------------------------
* ``issue_type`` : [Optional - default: ``Task``] Jira ticket type
* ``dedups`` : [Optional - default: ``fingerprint``] Tickets deduplication parameter. By default, Only one issue per ``fingerprint`` will be created. There can be more than one value to use. Possible values are: fingerprint, cluster_name, title, node, type, source, namespace, creation_date etc
* ``project_type_id_override`` : [Optional - default: None] If available, will override the ``project_name`` configuration. Follow these `instructions <https://confluence.atlassian.com/jirakb/how-to-get-project-id-from-the-jira-user-interface-827341414.html>`__ to get your project id.
* ``issue_type_id_override`` : [Optional - default: None] If available, will override the ``issue_type`` configuration. Follow these `instructions <https://confluence.atlassian.com/jirakb/finding-the-id-for-issue-types-646186508.html>`__ to get your issue id.
* ``assignee`` : [Optional - default: None] Jira ID of the person that the issue is assigned to.
* ``epic`` : [Optional - default: None] Jira ID of the epic that the issue is linked to.

Following optional settings only work for Prometheus alerts:

* ``sendResolved`` : [Optional - default: false] If true, will transition a Jira issue to "Done" when the alert event contains a "resolved" status.
* ``reopenIssues`` : [Optional - default: false] If true, will reopen a "Done" Jira issue when an alerts fire with the same fingerprint. If false, a new issue will be created.
* ``doneStatusName`` : [Optional - default: 'Done'] The name of the "Done" status in Jira. Will be used to identify "Done" tasks in Jira.
* ``reopenStatusName`` : [Optional - default: 'To Do'] The name of the "To Do" status in Jira. Will be used to identify "To Do" tasks in Jira.
* ``noReopenResolution`` : [Optional - default: ''] The name of a target Jira resolution that, if present on a Jira issue, prevents Robusta from re-opening it. If this value is present, it makes Robusta ignore the ``reopenStatusName`` config.

Configuring the Jira sink
------------------------------------------------

| To avoid too many Jira tickets, it's recommended to use :ref:`Sink Matchers <sink-matchers>` to limit the number of created tickets.

| In the example below, tickets will be created only for the ``CPUThrottlingHigh`` and ``KubePodCrashLooping`` Prometheus alerts.

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
          - jira_sink:
            name: personal_jira_sink
            url: https://workspace.atlassian.net
            username: username
            api_key: api_key
            dedups: (OPTIONAL)
              - fingerprint
            assignee: user_id of the assignee(OPTIONAL)
            epic: epic_id(OPTIONAL)
            project_name: project_name
            scope:
              include:
                - identifier: [CPUThrottlingHigh, KubePodCrashLooping]

Save the file and run

.. code-block:: bash
   :name: cb-add-jira-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

Try the example below to recieve an alert notification in Jira.


Test your Jira Prometheus Integration
---------------------------------------

The command below creates a crashing pod which triggers the ``KubePodCrashLooping`` alert. This will cause a Jira ticket to be opened when using the above example.

.. code-block:: bash
   :name: KubePodCrashLooping test

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/crashpod/broken.yaml

.. note::

   * If creating issues by ``project_name`` or ``issue_type`` fails, try specifying the corresponding ids using ``project_type_id_override`` and ``issue_type_id_override``. Check Optional Settings above for details.
