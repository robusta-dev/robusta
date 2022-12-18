Track Kubernetes changes
=============================

Introduction
---------------
In this tutorial, we will track changes to Kubernetes objects using Robusta. You will learn how to:

* Specify which Kubernetes object to track
* Filter out noisy changes and only track certain YAML fields
* Notify about changes in Slack, MSTeams, and more
* Send a diff of exactly what changed in your cluster

Why Track Kubernetes Changes?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Change tracking is useful in medium and large sized organizations, where multiple teams deploy to the same cluster.
Some use cases:

* **DevOps and Platform Teams:** Track all changes to Ingresses and other sensitive cluster resources.
* **Developers:** Get notified each time your application is deployed to production.
* **Security and DevSecOps:** TODO

Step by step guide
---------------------

1. Install Robusta

2. Add the following Helm values to ``generated_values.yaml``:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_deployment_update: {}
      actions:
        - resource_babysitter:
            omitted_fields: []
            fields_to_monitor: ["spec.replicas"]

3. Upgrade Robusta's configuration with Helm:

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

4. Test it by scaling a deployment that exists in your cluster: (TODO: provide yaml and better demo)

.. code-block:: python

   kubectl scale --replicas NEW_REPLICAS_COUNT deployments/DEPLOYMENT_NAME

If everything was configured correctly, a Robusta notification will arrive, showing exactly what changed in the deployment:

.. image:: ../images/replicas_change.png
  :width: 600
  :align: center

As you can see, the notification includes precise details on what changed.

How it works
----------------
Every automation has three parts.

triggers:
    We chose ``on_deployment_update`` which runs whenever Kubernetes Deployments are updated

actions:
    We chose :ref:`Resource babysitter` which is a builtin action. That action has a parameter ``fields_to_monitor``.

sinks:
    We didn't configure any sinks, so output is sent to the default sink. This is usually Slack and/or the `Robusta UI <https://home.robusta.dev/ui/>`_.

Further customization
^^^^^^^^^^^^^^^^^^^^
Try changing the configuration to monitors changes to a deployment's image tag.

TODO: hint

Cleanup
^^^^^^^^^^
Remove the Robusta configuration you added and run an update.
