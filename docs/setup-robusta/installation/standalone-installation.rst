:tocdepth: 2
:globaltoc_collapse: false

Barebones Installation
####################################

*Estimated time: 5 minutes*

Install Robusta standalone, without integrating Prometheus. See Robusta's native capabilities.

.. warning::

   Most people should install with Prometheus and **not** follow this tutorial.

   Robusta is useful standalone, but Prometheus makes it even better!

Prerequisites
---------------------

* A :ref:`supported Kubernetes cluster <Supported Kubernetes Clusters>`
* Helm

.. include:: ../_questions.rst

.. jinja:: install_no_prometheus
   :header_update_levels:
   :file: setup-robusta/installation/_generate_config.jinja

.. include:: ./_helm_install.rst

See Robusta in action
------------------------------

Let's deploy a crashing pod. Robusta will identify the problem and notify us:

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
If you didn't enable the UI during installation, don't worry. You can enable it at any time by running ``robusta integrations ui``.

# TODO: will enabling it this way mess up the accountID?

Finally, clean up the crashing pod:

.. code-block:: bash
   :name: cb-delete-crashpod

   kubectl delete deployment crashpod


Next Steps
---------------------------------

1. Learn to :ref:`track Kubernetes changes with Robusta <Automation Basics>`
2. Learn to :ref:`improve Prometheus alerts with Robusta <Alert Enrichment>`
