Python Profiling
===========================

In this tutorial, you will use Robusta to troubleshoot a Python application running on Kubernetes. Specifically,
you will analyze which functions use the most CPU.

Doing it
^^^^^^^^^^^^^^^^^^

Let's run the ``python_profiler`` action builtin to Robusta.

You need a Python application to profile. Try using Robusta itself. Replace the pod name below with Robusta's
actual pod name.

.. code-block:: bash

    robusta playbooks trigger python_profiler name=robusta-runner-8f4558f9b-pcbj9 namespace=default seconds=5

Seeing the result
^^^^^^^^^^^^^^^^^^^^

You should receive a message (by default in Slack) with the profile results.

.. image:: /images/python-profiler.png
  :width: 600
  :align: center

You can learn how to read the output in Brendan Gregg's excellent `blogpost on flamegraphs <https://www.brendangregg.com/FlameGraphs/cpuflamegraphs.html>`_.

Learn more
^^^^^^^^^^^^^^^^^^^

* :ref:`All python troubleshooting actions <Python troubleshooting>`
* :ref:`Manual Triggers`
