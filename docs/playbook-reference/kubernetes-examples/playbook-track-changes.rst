Track Kubernetes Changes
############################################

Robusta lets you get notifications when Kubernetes resources are updated. Users can set up personalized notifications for any Deployment, ReplicaSet, or other resource, ensuring you get notified when new versions are rolled out or other engineers change something important in the cluster. This feature is especially useful for various roles:

* **DevOps and Platform Teams** can track all changes to Ingresses and other sensitive cluster resources.
* **Developers** can receive notifications each time their application is deployed to production.
* **Security and DevSecOps** professionals can track changes to ClusterRoles or ServiceAccounts.

How to Track Changes in Kubernetes Resources
------------------------------------------------
1. **Create Custom Playbook**: Start by defining a personalized template that specifies when you should be notified and what data you'd like to see. This is your "custom playbook."
2. **Select Kubernetes Object**: In your custom playbook, specify which Kubernetes resource you want to monitor, such as Deployment or ReplicaSet.
3. **Filter YAML Fields**: To avoid unnecessary notifications, select specific YAML field. For example, when tracking an autoscaled Deployment, you can filter out notifications related to `Deployment.spec.replicas`, as this field is automatically updated by the Horizontal Pod Autoscaler (HPA) regularly.
4. **Set Up Change Detection**: Configure your playbook to send a 'diff' that shows exactly what changed in the selected Kubernetes object.
5. **Route Alerts (Optional)**: If needed, direct these change notifications to specific destinations, also known as 'Sinks', by adding this information to your custom playbook.

Kubernetes Change Tracking Use Cases
-----------------------------------------
Let's explore practical use cases for Kubernetes change tracking.


Use Case 1: Notification on Deployment Image Change
*******************************************************
**Scenario**: You want to be notified when a Deployment strategy or container details are changed.

**Implementation**:

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_deployment_update:
            change_filters:
              ignore: # These are ignored by default
              - status
              - metadata.generation
              - metadata.resourceVersion
              - metadata.managedFields
              - spec.replicas
              include:
                - spec.template.spec.containers[0]
                - spec.strategy
      actions:
        - resource_babysitter: {}
        - customise_finding:
            severity: HIGH
            title: "New changes in $kind/$namespace/$name"
      sinks:
        - some_sink_name # Optional

.. details:: How does it work?

  1. **Initialize Custom Playbook**: Create a custom playbook where you'll outline the rules for when and how you'll be notified.
  2. **Set Up the Deployment Trigger**: In your custom playbook, add the ``on_deployment_update`` trigger. This ensures you'll receive notifications for deployment changes.
  3. **Specify Fields to Monitor**: Add change_filters to your ``on_deployment_update`` trigger to filter which changes you will be notified for.
  4. **Route Notifications (Optional)**: Optionally, specify in your playbook where these notifications should be sent by defining 'sinks'.

Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

**Note**: You can also use the :ref:`Sink Matchers<sink-matchers>` to route notifications instead of explicitly specifying a sink in the playbook.


**Testing**:

Modify the image of a deployment in your cluster.

Run the following YAML files to simulate a deployment image change

.. code-block:: yaml

  kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/deployment_image_change/before_image_change.yaml
  kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/deployment_image_change/after_image_change.yaml

A Robusta notification will arrive in your configured :ref:`sinks <Sinks Reference>`, showing exactly what changed in the deployment.

**Sample Alert**:

.. image:: /images/deployment-image-change.png
  :width: 600
  :align: center


Use Case 2: Notification on Ingress Rules Change
*****************************************************************
**Scenario**: You want to be notified when an Ingress rules or tls details are changed.

**Implementation**:

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_ingress_all_changes:
            change_filters:
              ignore:
                - status
                - metadata.generation
                - metadata.resourceVersion
                - metadata.managedFields
                - spec.replicas
              include:
                - spec.rules
                - spec.tls
      actions:
        - resource_babysitter: {}
      sinks:
        - some_sink_name # Optional

.. details:: How does it work?

  1. **Initialize Custom Playbook**: Create a custom playbook where you'll outline the rules for when and how you'll be notified.
  2. **Set Up the Ingress Trigger**: In your custom playbook, add the ``on_ingress_all_changes`` trigger. This ensures you'll receive notifications for all ingress changes.
  3. **Specify Fields to Monitor**: Add change_filters to your ``on_ingress_all_changes`` trigger to filter which changes you will be notified for.
  4. **Route Notifications (Optional)**: Optionally, specify in your playbook where these notifications should be sent by defining 'sinks'.

Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

**Note**: You can also use the :ref:`Sink Matchers<sink-matchers>` to route notifications instead of explicitly specifying a sink in the playbook.

**Testing**:

Create, modify, or delete an ingress in your cluster.

Run the following commands to simulate ingress changes:

.. code-block:: yaml

  kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/ingress_port_path_change/before_port_path_change.yaml
  kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/ingress_port_path_change/after_port_path_change.yaml

A Robusta notification will arrive in your configured :ref:`sinks <Sinks Reference>`, showing exactly what changed in the ingress.

**Sample Alert**:

.. image:: /images/ingress-image-change.png
  :width: 600
  :align: center

Use Case 3: Notification when a Deployment image change - including the Deployment manifest
********************************************************************************************
**Scenario**: You want to get the Deployment manifest, each time the image changes

**Implementation**:

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_deployment_update:
          change_filters:
            include:
            - image
      actions:
      - json_change_tracker:
          url: "https://SOME-WEBHOOL-URL"

.. details:: How does it work?

  1. **Initialize Custom Playbook**: Create a custom playbook where you'll outline the rules for when and how you'll be notified.
  2. **Set Up the Deployment Trigger**: In your custom playbook, add the ``on_deployment_change`` trigger, with a ``scope`` including only image changes. This ensures you'll receive notifications for deployment image changes.

This playbook doesn't use a Sink! It sends the to the url specified in the action parameters.

Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

**Testing**:

Modify a Deployment image in your cluster.

A notification with the Deployment manifest, as json, should be sent to the webhook url



Cleanup
------------------------------
Remove the playbook you added based on your specific use case from the ``customPlaybooks`` in your ``generated_values.yaml`` file. Then, perform a :ref:`Helm Upgrade <Simple Upgrade>`.

.. Use Case 2: Notification on Kubernetes Job Failure
.. *******************************************************
.. **Scenario**: You want to be notified when a Kubernetes job is failed.

.. .. admonition:: Avoid Duplicate Alerts

..     If you installed Robusta with the embedded Prometheus stack, you don't need to configure this playbook. It's configured by default.


.. **Implementation**:

.. Add the following YAML to the ``customPlaybooks`` Helm value:

.. .. code-block:: yaml

..     customPlaybooks:
..     - triggers:
..       - on_job_failure: {} # (1)
..       actions:
..       - create_finding: # (2)
..           title: "Job Failed"
..           aggregation_key: "JobFailure"
..       - job_info_enricher: {} # (3)
..       - job_events_enricher: {} # (4)
..       - job_pod_enricher: {} # (5)
..       sinks:
..       - some_sink_name

..     1. :ref:`on_job_failure<on_job_failure>` fires once for each failed Kubernetes Job
..     2. :ref:`create_finding<create_finding>` generates a notification message
..     3. :ref:`job_info_enricher<job_info_enricher>` fetches the Jobs status and information
..     4. :ref:`job_events_enricher<job_events_enricher>` runs ``kubectl get events``, finds Events related to the Job, and attaches them
..     5. :ref:`job_pod_enricher<job_pod_enricher>` finds Pods that were part of the Job. It attaches Pod-level information like Pod logs

.. .. details:: How does it work?

..   1. **Initialize Custom Playbook**: Create a custom playbook where you'll define the rules for when and how you'll be notified.
..   2. **Set Up the Failure Trigger**: In your custom playbook, add the `on_job_failure` trigger. This will notify you specifically when a job fails.
..   3. **Configure Notification Creation**: Within the same playbook, use the `create_finding` action and set the title to `Job Failed`. This will generate the actual notification.
..   4. **Include Additional Information**: Add `job_info_enricher`, `job_events_enricher`, and `job_pod_enricher` to your playbook. These gather more details that will accompany your notification.
..   5. **Route Notifications (Optional)**: If desired, specify in your playbook where to send these notifications by adding 'sinks'.


.. Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

.. **Note**: You can also use the :ref:`Sink Matchers<sink-matchers>` to route notifications instead of explicitly specifying a sink in the playbook.

.. **Testing**:
.. Deploy a failing job. The job will fail after 60 seconds, then attempt to run again. After two attempts, it will fail for good.

.. .. code-block:: yaml

..     kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/job_failure/job_crash.yaml


.. **Sample Alert**:

.. .. image:: /images/failingjobs.png
..     :alt: Failing Kubernetes jobs notification on Slack
..     :align: center
