Customizing built-in playbooks
##############################

Robusta is a powerful `rules engine` for devops, but it needs rules or "playbooks" to tell it what to do.
Lets see how we can customize the broad collection of builtin playbooks.

Setting up a playbooks directory
-------------------------------------------------------------
You will need a `playbooks` directory with default files before continuing. There are three ways to set one up:

1. If you installed Robusta using ``robusta install``, you already have a `playbooks` directory in the working directory.
2. You can download your `playbooks` directory from your cluster by running ``robusta playbooks pull``
3. You can setup a new playbooks directory by running ``robusta examples``

.. warning::
    If you use ``robusta examples`` then `playbooks/active_playbooks.yaml` wont contain your API keys. Make sure to copy them over using ``robusta playbooks show-config``

A playbooks directory contains python scripts and one file named ``active_playbooks.yaml``. The python defines the *available* playbooks
and the yaml activates them.

Enabling a new playbook
------------------------

Lets edit ``active_playbooks.yaml`` and add the following:

.. code-block:: yaml

   (...)
   active_playbooks:
     (...)
     - name: "deployment_babysitter"
       action_params:
         fields_to_monitor: ["spec.replicas"]


This will add an additional playbook named **deployment_babysitter** - a playbook that monitors changes to deployments.
Don't remove the other playbooks in ``active_playbooks.yaml``. We want to add a new playbook, not remove the old ones.

Deploy your new config
------------------------
So far we have edited the configuration file locally. Now lets deploy it to Robusta inside your Kubernetes cluster.

From the playbooks directory run:

.. code-block:: python

   robusta playbooks deploy .

The **deployment_babysitter** playbook is now running. You will get a notification in Slack every time a deployment's number of replicas changes.

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
