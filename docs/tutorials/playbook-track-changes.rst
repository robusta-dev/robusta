.. TODO: add a tutorial for tracking ingresses

Track Kubernetes Changes
############################################

Let's track changes to Kubernetes objects using Robusta. Notifications will be sent to a :ref:`Sinks <Sinks Reference>`, like Slack or MSTeams.

In this tutorial you will:

* Specify which Kubernetes object to track
* Filter out noisy changes and only track certain YAML fields
* Send a diff of exactly what changed

.. details:: Why Track Kubernetes Changes?

    Change tracking is useful in organizations where multiple teams deploy to the same cluster. Some use cases:

    * **DevOps and Platform Teams:** Track all changes to Ingresses and other sensitive cluster resources.
    * **Developers:** Get notified each time your application is deployed to production.
    * **Security and DevSecOps:** Assorted use cases.

Defining a Playbook
---------------------

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_deployment_update: {}
      actions:
        - resource_babysitter:
            omitted_fields: []
            fields_to_monitor: ["spec.replicas"]

Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

Testing Your Playbook
------------------------

Scale a deployment that exists in your cluster:

Run the following YAML files to simulate a deployment change

.. code-block:: yaml

  kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/crashpod/healthy.yaml
  kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/crashpod/broken.yaml

A Robusta notification will arrive in your configured :ref:`sinks <Sinks Reference>`, showing exactly what changed in the deployment:

.. image:: /images/replicas_change.png
  :width: 600
  :align: center


How it Works
----------------
We configured a :ref:`custom playbook <What are Playbooks?>` with the trigger
:ref:`on_deployment_update <on_deployment_update>`. This trigger fires whenever Kubernetes Deployments are updated.

The trigger fires on *all* Deployment changes, even uninteresting changes to the Deployment's status performed by
Kubernetes itself on static clusters.

The action is :ref:`resource_babysitter<resource_babysitter>` action, which itself performs further filtering and
ignores uninteresting changes. This action is a little unusual - most of the time *triggers* perform all the filtering
and *actions* act on everything that reaches them.

In the future we're planning to improve the trigger mechanism so that filtering like ``fields_to_monitor`` moves out of
:ref:`resource_babysitter<resource_babysitter>` and into the ``on_deployment_update <on_deployment_update>` trigger
itself.


Adding Change Routing
------------------------------

To send change notifications to a *specific sink* instead of *all sinks*, you can choose between two methods:

1. Use :ref:`Sink Matchers<sink-matchers>`
2. Explicitly specify a sink in the playbook

Here is the latter method:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_deployment_update: {}
      actions:
      - resource_babysitter:
          omitted_fields: []
          fields_to_monitor: ["spec.replicas"]
      sinks:
      - some_sink_name


Check Your Understanding
------------------------------
Change the playbook configuration so it monitors changes to any Pod's image,
whether that Pod is part of a Deployment or not.

.. details:: Solution

    TODO: show solution

Cleanup
------------------------------
Remove this playbook from ``customPlaybooks`` and perform a :ref:`Helm Upgrade <Simple Upgrade>`.
