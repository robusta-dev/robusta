Java Troubleshooting
######################################################

In this tutorial, you will use Robusta to troubleshoot a java application running on Kubernetes. Specifically,
you will be remotely running functions from a custom JDK on any Java application.

Doing it
---------------------------------------

Let's run the ``java_process_inspector`` action builtin to Robusta.

| You need a Java application to debug. Look at ``test_pod_config.yaml`` in Robusta's ``java_toolkit`` repository for a demo Java application.
| Replace the pod name below with the Java applications pod actual pod name.

.. code-block:: bash

    robusta playbooks trigger java_process_inspector name=test-java-pod namespace=default
java-troubleshooting.rst

Seeing the result
-------------------------------------

You should receive a message (by default in Slack) with the JDK options to run on your pod.

.. image:: /images/java_process_inspector.png
  :width: 600
  :align: center


Learn more
------------------

* :ref:`Manual Triggers`
