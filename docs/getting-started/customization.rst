Enabling built-in playbooks
###########################

By itself, Robusta does nothing. It needs playbooks which define automated maintenance operations.

Lets customize Robusta and enable another playbook:

Editing Robusta's config
------------------------

While :ref:`Installing Robusta` you downloaded an example playbooks directory. Edit the ``active_playbooks.yaml`` in that directory:

.. code-block:: python

   global_config:
     slack_channel: "general"
   active_playbooks:
     - name: "deployment_babysitter"
       action_params:
         fields_to_monitor: ["spec.replicas"]

     - name: "restart_loop_reporter"
       action_params:
         restart_count_trigger: 2
         restart_reason: "CrashLoopBackOff"

The configuration above defines two playbooks:

* Deployment babysitter - a playbook that monitors changes to deployments
* Crash loop reporter - the playbook you saw during installation

Deploy your new config
------------------------
We've edited the configuration file locally, but the brain of Robusta runs inside your Kubernetes cluster. Lets deploy our new configuration to Kubernetes:

From the playbooks directory run:

.. code-block:: python

   robusta deploy .

The two playbooks you configured are now running. You will get a notification in Slack every time a pod enters a CrashLoopBackOff and every time a deployment's number of replicas changes.

Seeing your new config in action
----------------------------------
Scale one of your deployments using the command below:

.. code-block:: python

   kubectl scale --replicas NEW_REPLICAS_COUNT deployments/DEPLOYMENT_NAME

Now, open your 'general' slack channel. A deployment change notification should appear:

.. image:: ../images/replicas_change.png

How it works
----------------------------------
In the playbooks configuration, we asked to get notified every time the ``'spec.replicas'`` field changes.

Scaling the deployment triggered a notification.

Try changing the configuration in ``active_playbooks.yaml`` so that Robusta monitors changes to a deployment's image tag too.
