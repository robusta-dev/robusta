Enrich Prometheus alerts
##############################

In this tutorial we will continue learning about Robusta automations. This time we will configure automations that enrich and remediate Prometheus alerts.

Robusta comes with many Prometheus enrichments that work out of the box. In this tutorial you will add an additional custom enrichment.

Pre-requisites
---------------------------------

Before you can enrich prometheus alerts, you must forward Prometheus alerts to Robusta.

The best way to do so, is to answer "YES" in the Robusta installation to using the bundled Prometheus. If you did **not** do so, see :ref:`Sending Alerts to Robusta` for alernatives.

Enriching alerts
-----------------

The base configuration in ``generated_values.yaml`` forwards all Prometheus alerts:

.. code-block:: yaml

   builtinPlaybooks:
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - default_enricher: {}

On top of this there are additional enrichments for specific alerts. (See :ref:`Insights Coverage`)

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