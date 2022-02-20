Java Troubleshooting
######################################################

In this tutorial, you will use Robusta to troubleshoot a java application running on Kubernetes.
This tool can be used to analyze memory in your java application or diagnose problems due to thread activity.


.. raw:: html

  <div style="position: relative; padding-bottom: 62.5%; height: 0;"><iframe src="https://www.youtube.com/embed/DaxgfLp14vE" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

Doing it
---------------------------------------

Let's run the ``java_process_inspector`` action builtin to Robusta.

| You need a Java application to debug.
| To create our demo java application on your cluster run:

.. code-block:: bash

    kubectl apply -f https://github.com/robusta-dev/java_toolkit/blob/d3b32f3cabb3c416b404ca7231ff6ad7d5ffbc8d/java_test_pod/test_pod_config.yaml``

| For debugging your own pod replace the pod name below with the Java applications pod actual pod name.

.. code-block:: bash

    robusta playbooks trigger java_process_inspector name=test-java-pod namespace=default


Seeing the result
-------------------------------------

You should receive a message (by default in Slack) with the troubleshooting options to run on your pod.

.. image:: /images/java_process_inspector.png
  :width: 600
  :align: center


From here you can debug the memory in your Java application with jmap or diagnose problems with thread activity via jstack

Learn more
------------------

* :ref:`Java Troubleshooting Actions`
* :ref:`Manual Triggers`
