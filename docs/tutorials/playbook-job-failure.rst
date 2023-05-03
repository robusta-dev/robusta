Track Failed Kubernetes Jobs
##############################

Lets track failing Kubernetes Jobs and notify the user. Notifications will be sent to all configured :ref:`Sinks <Sinks Reference>`
like Slack, MSTeams, or DataDog. It is also possible to :ref:`route notifications to specific sinks<Routing Alerts to Specific Sinks>`.

Defining a Playbook
------------------------------------------

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_job_failure: {}
      actions:
      - create_finding:
          title: "Job Failed"
          aggregation_key: "job_failure"
      - job_info_enricher: {}
      - job_events_enricher: {}
      - job_pod_enricher: {}

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Testing Your Playbook
------------------------------------------

Deploy a failing job. The job will fail after 60 seconds, then attempt to run again. After two attempts, it will fail for good.

.. code-block:: yaml

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/job_failure/job_crash.yaml

.. details:: Output

    .. image:: /images/failingjobs.png
        :alt: Failing Kubernetes jobs notification on Slack
        :align: center


How it Works
-------------

This playbook uses the :ref:`on_job_failure` trigger, that fires once for each Job failure.

It uses the :ref:`create_finding <create_finding>` action to generate a notification message, and three additional actions to
attach extra information: :ref:`job_info_enricher <job_info_enricher>`, :ref:`job_events_enricher <job_events_enricher>`,
and :ref:`job_pod_enricher <job_pod_enricher>`.

Avoiding Duplicate Notifications
------------------------------------------
Many Prometheus installations include a default alert to track failing Kubernetes Jobs.

When using Robusta, you can disable that Prometheus alert or you can use the ``on_prometheus_alert`` trigger instead
of the ``on_job_failure`` trigger to avoid a duplicate. Robusta does something similar out of the box.
