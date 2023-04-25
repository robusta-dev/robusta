See Robusta in action
------------------------------

Let's deploy a crashing pod:

.. code-block:: bash
   :name: cb-apply-crashpod

   kubectl apply -f https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw

Verify that the pod is actually crashing:

.. code-block:: console
   :name: cb-verify-crash-pod-crashing

   $ kubectl get pods -A | grep crashpod
   NAME                            READY   STATUS             RESTARTS   AGE
   crashpod-64d8fbfd-s2dvn         0/1     CrashLoopBackOff   1          7s

Once the pod has reached two restarts, you'll get notified in Slack (or whatever alternative integration you configured):

.. admonition:: Example Slack Message

    .. image:: /images/crash-report.png


Now open the `Robusta UI <https://platform.robusta.dev/>`_ and look for the same message there.

Finally, clean up the crashing pod:

.. code-block:: bash
   :name: cb-delete-crashpod

   kubectl delete deployment crashpod
