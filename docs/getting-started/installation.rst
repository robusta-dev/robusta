Installation Guide
##################

Generating a Config File
-----------------------------------------------------
Before we can install Robusta, we need to configure it. This is easily done by installing the Robusta cli:

.. code-block:: bash

   pip3 install -U robusta-cli --no-cache

And generating an ``active_playbooks_generated.yaml`` file:

.. code-block:: bash

   robusta gen-config

.. note:: If pip fails due to a permissions error, either run the command as root or append ``--user`` to the command.

Installing Robusta with Helm
-----------------------------------------------------
We can install Robusta using `helm <https://helm.sh/>`_ and the config file you just generated:

.. code-block:: bash

    helm repo add robusta https://robusta-charts.storage.googleapis.com
    helm install robusta robusta/robusta --set-file playbooks_file=./active_playbooks_generated.yaml

This will install two deployments in the current namespace.
Robusta can be removed at any time by running ``helm uninstall robusta``. :ref:`Learn more about Robusta's architecture<Robusta Architecture>`.

Seeing Robusta in Action
------------------------------
By default, Robusta sends Slack notifications when Kubernetes pods crash. Run the following command to create a crashing pod:

.. code-block:: python

   kubectl apply -f https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw/crashpod.yaml

Verify that the pod is actually crashing:

.. code-block:: bash

   $ kubectl get pods -A
   NAME                            READY   STATUS             RESTARTS   AGE
   crashpod-64d8fbfd-s2dvn         0/1     CrashLoopBackOff   1          7s


Once the pod has reached two restarts, you should see the following message in your Slack channel:

.. image:: /images/crash-report.png

Don't forget to clean up the crashing pod:

.. code-block:: python

   kubectl delete deployment -n robusta crashpod

