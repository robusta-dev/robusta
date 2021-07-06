Customizing built-in playbooks
##############################

By itself, Robusta does nothing. All of it's power comes from playbooks. Lets customize that set of playbooks.

Downloading Playbooks
-------------------------------------------------------------
First, download the base set of playbooks:

.. code-block:: python

   robusta examples

We now a have `./playbooks` directory that we can customize and upload back to Robusta.

Lets take a closer look at that directory.

`./playbooks` contains several python scripts and one file named `active_playbooks.yaml`. The python scripts define the *available* playbooks
and the yaml file defines which playbooks are actually in use and how they are configured.

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


This will add an additional playbook named **Deployment babysitter** - a playbook that monitors changes to deployments.
Don't remove the other playbooks in ``active_playbooks.yaml``. We want to add a new playbook, not remove the old ones.

Deploy your new config
------------------------
We've edited the configuration file locally, but the brain of Robusta runs inside your Kubernetes cluster. Lets deploy our new configuration to Kubernetes:

From the playbooks directory run:

.. code-block:: python

   robusta deploy .

The new playbook you configured is now running. You will get a notification in Slack every time a deployment's number of replicas changes.

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
