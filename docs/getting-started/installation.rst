Installing Robusta
##################

Installing the Robusta cli
-----------------------------------------------------

The recommend way to install Robusta is to first install the client-side CLI command and then use that to install robusta in your cluster. First, install the cli:

.. code-block:: python

   pip3 install -U robusta-cli --no-cache

If you encounter a permissions error, you can either re-run the above command as root or append ``--user`` to the command.

Try running ``robusta --help`` to see what the robusta cli can do.

Installing Robusta in a Kubernetes cluster.
-----------------------------------------------------
.. note:: ``robusta`` and ``helm`` commands use your current kubectl context. Use ``kubectl config use-context`` to change it.

Robusta is installed using ``helm``.

First, get a copy of Robusta's ``helm`` chart

.. code-block:: bash

    helm repo add robusta https://robusta-charts.storage.googleapis.com

Now, use the Robusta cli generate the initial configuration

.. code-block:: bash

    robusta gen-config

This will generate a configuration file named ``active_playbooks_generated.yaml``

Lastly, use that configuration to install robusta

.. code-block:: bash

    helm install robusta robusta/robusta --set-file playbooks_file=./active_playbooks_generated.yaml

This will install two deployments in the ``robusta`` namespace.
Robusta can be removed at any time by running ``helm uninstall robusta``. :ref:`Learn more about Robusta's architecture<Robusta Architecture>`.

Seeing Robusta in Action
------------------------------
Lets try out a default playbook which sends Slack notifications whenever pods crash. Run the following command to create a crashing pod:

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

