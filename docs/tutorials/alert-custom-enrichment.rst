Enrich Custom Prometheus Alerts
##############################

In the last tutorial we defined a custom Prometheus alert.

We now configure a Robusta playbook to enhance that alert.

Prerequisites
---------------------------------

.. Complete the previous tutorial, :ref:`Define Custom Prometheus Alerts`.
You must have some Prometheus alerts already defined. Ex: HostHighCpuLoad


Enriching a Custom Alert
--------------------------------

Define a :ref:`customPlaybook <customPlaybooks>` that responds to our Prometheus alert:

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: HostHighCpuLoad
     actions:
     - node_bash_enricher:
         bash_command: ps aux

.. warning::

    Defining a customPlaybook for a specific alert, wont stop other playbooks from seeing that alert too.

    Playbooks run in the order they appear in ``customPlaybooks``.

    To stop processing after some action, set the ``stop`` parameter:

    .. code-block:: yaml

       customPlaybooks:
       - triggers:
         - on_prometheus_alert:
             alert_name: HostHighCpuLoad
         actions:
         - node_cpu_enricher: {}
         stop: True
       - triggers:
         - on_prometheus_alert: {}
         actions:
         - some_other_action: {}

    Using this configuration, ``some_other_action`` wont run for ``HostHighCpuLoad``.

Further Reading
---------------

* View all :ref:`Prometheus Enrichment <Prometheus Enrichers> actions`
