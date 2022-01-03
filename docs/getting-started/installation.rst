Installation Guide
##################

Robusta is installed with Helm. You can handwrite the values.yaml, but it is easier to autogenerate it.

Helm Installation
------------------------------

1. Download the Helm chart and generate a Robusta configuration. This will setup Slack and other integrations.

.. code-block:: bash

   helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
   python3 -m pip install -U robusta-cli --no-cache
   robusta gen-config

2. Save ``generated_values.yaml``, somewhere safe. This is your Helm ``values.yaml`` file.

3. Install Robusta using Helm:

.. code-block:: bash

    helm install robusta robusta/robusta -f ./generated_values.yaml

4. Verify that Robusta installed two deployments in the current namespace:

.. code-block:: bash

    kubectl get pods

.. admonition:: Common errors
    :class: caution

    * Permissions error: re-run the command as root or append ``--user`` to the command
    * ``robusta`` not found error: add `Python's script directory to PATH <https://www.makeuseof.com/python-windows-path/>`_ before you run ``robusta gen-config``

Seeing Robusta in action
------------------------------

By default, Robusta sends Slack notifications when Kubernetes pods crash.

1. Create a crashing pod:

.. code-block:: python

   kubectl apply -f https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw


2. Verify that the pod is actually crashing:

.. code-block:: bash

   $ kubectl get pods -A
   NAME                            READY   STATUS             RESTARTS   AGE
   crashpod-64d8fbfd-s2dvn         0/1     CrashLoopBackOff   1          7s

3. Once the pod has reached two restarts, check your Slack channel for a message about the crashing pod.

.. admonition:: Example Slack Message

    .. image:: /images/crash-report.png


4. Clean up the crashing pod:

.. code-block:: python

   kubectl delete deployment crashpod

This example was pretty basic. :ref:`Let's see a more complicated example. Something you can't do easily without Robusta. <Example Playbook>`