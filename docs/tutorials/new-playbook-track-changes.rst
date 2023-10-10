.. TODO: add a tutorial for tracking ingresses

Track Kubernetes Changes
############################################

Robusta lets you get notifications when Kubernetes resources are updated. Users can setup personalized notifications for any Deployment, ReplicaSet, or other resource, ensuring you get notified when new versions are rolled out or other engineers change something important in the cluster. For example

* **DevOps and Platform Teams:** Track all changes to Ingresses and other sensitive cluster resources.
* **Developers:** Get notified each time your application is deployed to production.
* **Security and DevSecOps:** Assorted use cases.

.. Let's track changes to Kubernetes objects using Robusta. Notifications will be sent to a :ref:`Sinks <Sinks Reference>`, like Slack or MSTeams.
.. Users can choose what to track and what information to recieve in an alert using Playbooks. :ref:`Read more about playbooks<What are Playbooks?>`

Steps to track changes
--------------------------
1. Define a custom template with when the alert should fire and what data you want. This personalized template is called a :ref:`"custom playbook"<Playbook Basics>`.
2. Specify which Kubernetes object to track.
3. Only track certain YAML fields and filter out noisy changes.
4. Send a diff of exactly what changed.
5. Optional - Route the changes to specific destinations(Sinks).


Kubernetes Change Tracking Use Cases
--------------------------------------
Let's explore practical use cases for Kubernetes change tracking.


Use Case 1: Alert on Deployment Image Change
***********************************************

**Scenario**: When a Deployment's image is changed, you want to get notified with information about the change.

**Solution**:

1. Create a custom playbook
2. Add the `on_deployment_update` trigger. It notifies you on all deployment changes.
3. Use the `resource_babysitter` action with `images` in the `fields_to_monitor` option. This elimiates noisy changes.
4. Optional - Route alerts to specific sinks


**Implementation**:

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_deployment_update: {}
      actions:
        - resource_babysitter:
            omitted_fields: []
            fields_to_monitor: ["images"]
      sinks:
      - some_sink_name #Optional

Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

**Note**: You can also use the :ref:`Sink Matchers<sink-matchers>` to route notifications instead of explicitely specifying a sink in the playbook.


**Testing**:

Modify the image of a deployment in your cluster.

Run the following YAML files to simulate a deployment image change

.. code-block:: yaml

  kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/deployment_image_change/after_image_change.yaml
  kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/deployment_image_change/after_image_change.yaml

A Robusta notification will arrive in your configured :ref:`sinks <Sinks Reference>`, showing exactly what changed in the deployment.

**Sample Alert**:

.. image:: /images/deployment-image-change.png
  :width: 600
  :align: center

Use Case 2: Alert on Kubernetes Job Failure
***********************************************
**Scenario**: When a Kubernetes Job is failed, you want an alert with information related to the failed job.

**Solution**:

1. Create a custom playbook
2. Add the `on_job_failure` trigger. It notifies you when a job is failed.
3. Use the `create_finding` action to create an alert wih the title `Job Failed`.
4. Add `job_info_enricher`, `job_events_enricher`, `job_pod_enricher` to gather additional information to be sent with the alert.
5. Optional - Route alerts to specific sinks

.. admonition:: Avoid Duplicate Alerts

    If you installed Robusta with the embedded Prometheus stack, you don't need to configure this playbook. It's configured by default.


**Implementation**:

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_job_failure: {}  # (1)
      actions:
      - create_finding: # (2)
          title: "Job Failed"
          aggregation_key: "job_failure"
      - job_info_enricher: {} # (3)
      - job_events_enricher: {} # (4)
      - job_pod_enricher: {} # (5)
      sinks:
      - some_sink_name

.. code-annotations::
    1. :ref:`on_job_failure<on_job_failure>` fires once for each failed Kubernetes Job
    2. :ref:`create_finding<create_finding>` generates a notification message
    3. :ref:`job_info_enricher<job_info_enricher>` fetches the Jobs status and information
    4. :ref:`job_events_enricher<job_events_enricher>` runs ``kubectl get events``, finds Events related to the Job, and attaches them
    5. :ref:`job_pod_enricher<job_pod_enricher>` finds Pods that were part of the Job. It attaches Pod-level information like Pod logs

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

**Note**: You can also use the :ref:`Sink Matchers<sink-matchers>` to route notifications instead of explicitely specifying a sink in the playbook.

**Testing**:
Deploy a failing job. The job will fail after 60 seconds, then attempt to run again. After two attempts, it will fail for good.

.. code-block:: yaml

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/job_failure/job_crash.yaml


**Sample Alert**:

.. image:: /images/failingjobs.png
    :alt: Failing Kubernetes jobs notification on Slack
    :align: center

.. How it Works
.. ----------------
.. We configured a :ref:`custom playbook <What are Playbooks?>` with the trigger
.. :ref:`on_deployment_update <on_deployment_update>`. This trigger fires whenever Kubernetes Deployments are updated.

.. The trigger fires on *all* Deployment changes, even uninteresting changes to the Deployment's status performed by
.. Kubernetes itself on static clusters.

.. The action is :ref:`resource_babysitter<resource_babysitter>` action, which itself performs further filtering and
.. ignores uninteresting changes. This action is a little unusual - most of the time *triggers* perform all the filtering
.. and *actions* act on everything that reaches them.

.. In the future we're planning to improve the trigger mechanism. Filters like ``fields_to_monitor`` will move from the
.. :ref:`resource_babysitter<resource_babysitter>` into triggers like `on_deployment_update <on_deployment_update>`.

.. Adding Change Routing
.. ------------------------------

.. To send change notifications to a *specific sink* instead of *all sinks*, you can choose between two methods:

.. 1. Use :ref:`Sink Matchers<sink-matchers>`
.. 2. Explicitly specify a sink in the playbook

.. Here is the latter method:

.. .. code-block:: yaml

..     customPlaybooks:
..     - triggers:
..       - on_deployment_update: {}
..       actions:
..       - resource_babysitter:
..           omitted_fields: []
..           fields_to_monitor: ["spec.replicas"]
..       sinks:
..       - some_sink_name


.. Check Your Understanding
.. ------------------------------
.. Change the playbook configuration so it monitors changes to any Pod's image,
.. whether that Pod is part of a Deployment or not.

.. .. details:: Solution

..     TODO: show solution

Cleanup
------------------------------
Remove this playbook from ``customPlaybooks`` and perform a :ref:`Helm Upgrade <Simple Upgrade>`.
