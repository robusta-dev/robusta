Track Failed Kubernetes Jobs
##############################

Notify about failed Kubernetes Jobs in Slack, MSTeams, DataDog, or other :ref:`Sinks <Sinks Reference>`.

.. image:: /images/failingjobs.png
    :alt: Failing Kubernetes jobs notification on Slack
    :align: center

.. admonition:: Avoid Duplicate Alerts

    If you installed Robusta with the embedded Prometheus stack, you don't need to configure this playbook. It's configured by default.

Defining a Playbook
------------------------------------------

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_job_failure: {} # (1)
      actions:
      - create_finding: # (2)
          title: "Job Failed"
          aggregation_key: "JobFailure"
      - job_info_enricher: {} # (3)
      - job_events_enricher: {} # (4)
      - job_pod_enricher: {} # (5)

.. code-annotations::
    1. :ref:`on_job_failure<on_job_failure>` fires once for each failed Kubernetes Job
    2. :ref:`create_finding<create_finding>` generates a notification message
    3. :ref:`job_info_enricher<job_info_enricher>` fetches the Jobs status and information
    4. :ref:`job_events_enricher<job_events_enricher>` runs ``kubectl get events``, finds Events related to the Job, and attaches them
    5. :ref:`job_pod_enricher<job_pod_enricher>` finds Pods that were part of the Job. It attaches Pod-level information like Pod logs
    
Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Testing Your Playbook
------------------------------------------

Deploy a failing job. The job will fail after 60 seconds, then attempt to run again. After two attempts, it will fail for good.

.. code-block:: yaml

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/job_failure/job_crash.yaml

Tips and Tricks
----------------

Route failed Jobs to specific Slack channels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Refer to :ref:`docs on notification routing<Routing Alerts to Specific Sinks>`.
