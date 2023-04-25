Silencing Alerts
=============================

Prometheus Alerts can be silenced several ways:

* Define a *silence* in Prometheus according to alert labels
* Clicking the *Silence* button in Slack (this is equivalent to the above method)
* Define a Robusta playbook with a *smart silencer action*

Robusta silencers are useful for:

* Implementing *silencing as code* in a YAML file
* Selectively silencing with *smart logic*, not just according to labels

Using Silencer Actions
------------------------------------------------

Here is an example that shows the power of silencer actions.

Let's silence the `KubePodCrashLooping` alert when it fires within 10 minutes of a node restart:

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: KubePodCrashLooping
     actions:
     - node_restart_silencer:
         post_restart_silence: 600 # seconds

The *node_restart_silencer* is context-aware. It will only silence ``KubePodCrashLooping`` for Pods running on the
node that just restarted.

Further Reading
-----------------

* View all :ref:`Prometheus Silencer <Prometheus Silencers>` actions
