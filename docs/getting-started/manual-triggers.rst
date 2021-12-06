Manual Triggers
##############################

So far, all the playbooks you've seen respond to events in your cluster. You can also run playbooks on demand.

Manually triggering a playbook
-------------------------------
Let's profile a Python application in your cluster. Robusta itself is written in Python so we can profile that.

Get the name of the robusta-runner pod:

.. code-block:: bash

    $ kubectl get pods -A | grep robusta-runner
    default       robusta-runner-8f4558f9b-pcbj9


Trigger the ``python_profiler`` playbook via the robusta cli:

.. code-block:: bash

    robusta playbooks trigger python_profiler name=robusta-runner-8f4558f9b-pcbj9 namespace=default seconds=5

The profiler result will be sent to the sink. Here is an example result in Slack:

.. image:: /images/python-profiler.png
  :width: 600
  :align: center

How manual triggers work
----------------------------------
``python_profiler`` is just a regular action that takes a Pod as input. It can be run automatically:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_prometheus_alert:
            alert_name:  "HighCPU"
      actions:
        - python_profiler:
            seconds: 5

Or it can be run manually like we did here.

With manual triggers you have to provide yourself the name and namespace of Kubernetes resources the action needs.
We did so with the ``name`` and ``namespace`` cli parameters.

Full reference
---------------------------------

Most playbooks can be triggered manually as follows:

.. code-block:: bash

    robusta playbooks trigger <action_name> name=<name> namespace=<namespace> kind=<kind> <key>=<value>

The parameters above are:

name
    The name of a Kubernetes resource

namespace
    The resource's namespace

kind
    ``pod``, ``deployment``, or any other resource the action supports. This can be left out for playbooks that support
    one input type.

<key>=<value>
    Any additional parameters the action needs
