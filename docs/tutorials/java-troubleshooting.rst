Java jmap and stack
==================================

In this tutorial, you will use Robusta to troubleshoot a java application running on Kubernetes.

The following is currently supported:

1. Using jmap to troubleshoot memory leaks
2. Using jstack to get thread dumps

.. note::
    | GKE, AKS, and EKS are all supported.
    | As of now, KIND and Minikube are not yet supported.

.. raw:: html

  <div style="position: relative; padding-bottom: 62.5%; height: 0;"><iframe src="https://www.youtube.com/embed/DaxgfLp14vE" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

Doing it
^^^^^^^^^^^^^

You need a Java application to debug. To create a demo application on your cluster run:

.. code-block:: bash

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/java_toolkit/416d62ba6a6c6cb2e5270c4cf793d340b708b9ea/java_test_pod/test_pod_config.yaml


Now run a Robusta troubleshooting action called ``java_process_inspector``. Make sure to replace the pod's name below with the actual pod name:

.. code-block:: bash

    robusta playbooks trigger java_process_inspector name=test-java-pod namespace=default

You should receive a message (by default in Slack) with the troubleshooting options to run on your pod.

.. image:: /images/java_process_inspector.png
  :width: 600
  :align: center

Click the buttons in Slack to run jmap or jstack. See :ref:`Java Troubleshooting Actions` for more information on what each of the debugging choices do.

As an example, here is jmap output showing the application's memory usage:

.. image:: /images/pod_jmap_pid.png
  :width: 600
  :align: center

Learn more
^^^^^^^^^^^^^^

* :ref:`Java Troubleshooting Actions`
* :ref:`Manual Triggers`
