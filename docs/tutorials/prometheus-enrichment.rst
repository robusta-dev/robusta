Improve Prometheus Alerts
##############################

In this tutorial we will try out Robusta's features for handling Prometheus alerts in Kubernetes clusters.

Setup
---------------------------------

Before you can enrich prometheus alerts, you must forward Prometheus alerts to Robusta by adding a webhook receiver to AlertsManager.

See :ref:`Sending Alerts to Robusta` for details.

General tips
---------------
When trying out these features, you can leave your existing alerting Slack channel in place and add a new channel for
Robusta's improved Prometheus alerts. This will let you compare Robusta's alerting with Prometheus' builtin alerting.

Enriching alerts
-----------------

The base configuration in ``values.yaml`` forwards all Prometheus alerts:

.. code-block:: yaml

   builtinPlaybooks:
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - default_enricher: {}

On top of this there are additional enrichments for specific alerts.

You can also define your own enrichments using ``customPlaybooks``:

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: HostHighCpuLoad
     actions:
     - node_bash_enricher:
         bash_command: ps aux

In practice, you wont need to configure much. The default enrichments are good and will only improve with time.

.. warning::

    Note that adding an enricher to a specific alert, doesn't stop other enrichers from running.

    Enrichers will run by the order they appear in the values file.

    If for some reason, you would like to stop processing after some enricher, you can use the ``stop`` playbook parameter:

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

    Using this configuration, the ``some_other_action`` wont run for the ``HostHighCpuLoad`` alert.


Silencing alerts
------------------

Silencers are actions which prevent alerts from being sent to sinks.

We can silence `KubePodCrashLooping` alerts in the first ten minutes after a node (re)starts:

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: KubePodCrashLooping
     actions:
     - node_restart_silencer:
         post_restart_silence: 600 # seconds


Fixing alerts
---------------

This part of the tutorial is coming soon. For now, experiment with Robusta on Prometheus alerts listed in :ref:`Insights Coverage`