Installing Robusta
##################

Installing the Robusta cli
-----------------------------------------------------

The recommend way to install Robusta is to first install the client-side CLI command and then use that to install robusta in your cluster. First, install the cli:

.. code-block:: python

   pip3 install -U robusta-cli --force-reinstall --no-cache

If you encounter a permissions error, you can either re-run the above command as root or append ``--user`` to the command.

Congrats, you're halfway done installing robusta.

Try running ``robusta --help`` to see what the robusta cli can do.

Installing Robusta in a Kubernetes cluster.
-----------------------------------------------------
First, make sure you select the right Kubernetes context:

.. code-block:: bash

    kubectl config use-context <CLUSTER-TO-INSTALL-ON>


Then run:

.. code-block:: bash

   robusta install

This will deploy Robusta to your Kubernetes cluster and optionally setup Slack integration.

For details on what this command installs, see :ref:`Robusta Architecture`. Everything is installed in the `robusta` namespace
and therefore Robusta can be removed at any time by deleting that namespace.

If you would like to try out the Slack integration but don't use Slack or can't add the app to your workspace, we have demo Slack workspaces available for testing. Please contact us for details.

Deploy Robusta playbooks
-----------------------------

Robusta is now installed but it still doesn't have any playbooks. Playbooks contain logic, whereas Robusta itself handles event plumbing.

Lets download some sample playbooks and deploy them:

.. code-block:: python

   robusta examples
   robusta deploy playbooks/

Congrats! Robusta is now configured. You can stop here or you can read on for a short demo of what Robusta can do.

Seeing Robusta in Action
------------------------------
Lets try out a default playbook which sends a Slack notification whenever pods crash. First, run the following command to create a crashing pod:

.. code-block:: python

   kubectl apply -f https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw/crashpod.yaml

Lets verify we have a crashing pod:

.. code-block:: bash

   $ kubectl get pods -A
   NAME                            READY   STATUS             RESTARTS   AGE
   crashpod-64d8fbfd-s2dvn         0/1     CrashLoopBackOff   1          7s


Once the pod has reached two restarts, you should see the following message in your Slack channel:

.. image:: /images/crash-report.png

To finish, lets clean up the crashing pod:

.. code-block:: python

   kubectl delete deployment -n robusta crashpod

