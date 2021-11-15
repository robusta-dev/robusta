Manual Triggers
##############################

All the playbooks we have seen so far respond to events in your cluster.
You can also run playbooks on demand.

Example
-----------------
Let's manually profile a Python application in your cluster. No prior setup for the Python application is necessary!

We will need an example Python application to profile. The ``robusta-runner`` is written in Python and already
installed in your cluster, so we can profile that. First, get the name of the robusta-runner pod:

.. code-block:: bash

    $ kubectl get pods -A | grep robusta-runner
    default       robusta-runner-8f4558f9b-pcbj9


Now trigger the ``python_profiler`` playbook via the ``robusta`` cli:

.. code-block:: bash

    robusta playbooks trigger python_profiler name=robusta-runner-8f4558f9b-pcbj9 namespace=default

The profiler result will be sent to all default sinks. Here is an example result in Slack:

.. image:: /images/python-profiler.png
  :width: 600
  :align: center

