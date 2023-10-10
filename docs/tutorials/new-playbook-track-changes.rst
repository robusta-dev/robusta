.. TODO: add a tutorial for tracking ingresses

Track Kubernetes Changes
############################################

Robusta lets you get notifications when Kubernetes resources are updated. Users can setup personalized notifications for any Deployment, ReplicaSet, or other resource, ensuring you get notified when new versions are rolled out or other engineers change something important in the cluster. This feature is especially useful for various roles:

* **DevOps and Platform Teams** can track all changes to Ingresses and other sensitive cluster resources.
* **Developers** will receive notifications each time their application is deployed to production.
* **Security and DevSecOps** professionals benefit from assorted use cases, such as monitoring changes to security settings.

.. Let's track changes to Kubernetes objects using Robusta. Notifications will be sent to a :ref:`Sinks <Sinks Reference>`, like Slack or MSTeams.
.. Users can choose what to track and what information to recieve in an alert using Playbooks. :ref:`Read more about playbooks<What are Playbooks?>`

.. Steps to track changes
.. --------------------------
.. 1. Define a custom template with when the alert should fire and what data you want. This personalized template is called a :ref:`"custom playbook"<Playbook Basics>`.
.. 2. Specify which Kubernetes object to track.
.. 3. Only track certain YAML fields and filter out noisy changes.
.. 4. Send a diff of exactly what changed.
.. 5. Optional - Route the changes to specific destinations(Sinks).

How to Track Changes in Kubernetes Resources
---------------------------------------------
1. **Create a Custom Playbook**: Start by defining a personalized template that specifies when the alert should fire and what data you'd like to see. This is your "custom playbook."
2. **Select Kubernetes Object**: In your custom playbook, specify which Kubernetes resource you want to monitor, such as Deployment or ReplicaSet.
3. **Filter YAML Fields**: Choose specific YAML fields to track in order to avoid unnecessary alerts. Add these field filters to your custom playbook.
4. **Set Up Change Detection**: Configure your playbook to send a 'diff' that shows exactly what changed in the selected Kubernetes object.
5. **Route Alerts (Optional)**: If needed, direct these change notifications to specific destinations, also known as 'Sinks', by adding this information to your custom playbook.

Kubernetes Change Tracking Use Cases
--------------------------------------
Let's explore practical use cases for Kubernetes change tracking.


Use Case 1: Alert on Deployment Image Change
***********************************************
**Scenario**: You want to be notified when a Deployment's image is changed.

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

.. details:: How does it work?

  1. **Initialize Custom Playbook**: Create a custom playbook where you'll define your alert rules and conditions.
  2. **Set the Trigger**: Inside your custom playbook, add the `on_deployment_update` trigger. This ensures you'll get notifications for all changes to deployments.
  3. **Specify What to Monitor**: In the same playbook, use the `resource_babysitter` action and set `images` in the `fields_to_monitor` option. This filters out any irrelevant changes, focusing only on image updates.
  4. **Route Alerts (Optional)**: Optionally, you can also specify in your playbook where you'd like these alerts to be sent by defining 'sinks'.

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

.. details:: How does it work?

  1. **Initialize Custom Playbook**: Start by creating a custom playbook where you will outline the rules for when and how you'll be alerted.
  2. **Set Up the Failure Trigger**: In your custom playbook, add the `on_job_failure` trigger. This will notify you specifically when a job fails.
  3. **Configure Alert Creation**: Within the same playbook, use the `create_finding` action and set the alert title to `Job Failed`. This will generate the actual alert.
  4. **Include Additional Information**: Add `job_info_enricher`, `job_events_enricher`, and `job_pod_enricher` to your playbook. These gather more details that will accompany your alert for comprehensive information.
  5. **Route Alerts (Optional)**: If desired, specify in your playbook where to send these alerts by adding 'sinks'.


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
