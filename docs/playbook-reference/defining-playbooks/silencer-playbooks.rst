.. _Silencer Playbooks:

Silencer Playbooks
##################

Silencer playbooks prevent alerts from being sent by stopping playbook execution before notifications reach sinks.

They're useful for:

* Implementing *silencing as code* in a YAML file
* Selectively silencing with *smart logic*, not just according to labels
* Reducing alert noise by filtering expected transient conditions

How Silencers Work
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An action can :ref:`stop the processing flow <stop_processing>` if needed, preventing subsequent actions from being run.

Silencer actions evaluate conditions and stop alert propagation when those conditions are met. This prevents alerts from being sent to other playbooks and notification sinks.

**Important:** Silencers must be defined before other playbooks to work correctly. Only actions following the silencer will be stopped.

Example: Node Restart Silencer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This example silences ``KubePodCrashLooping`` alerts when they fire within 10 minutes of a node restart:

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: KubePodCrashLooping
     actions:
     - node_restart_silencer:
         post_restart_silence: 600 # seconds

The ``node_restart_silencer`` is context-aware. It will only silence ``KubePodCrashLooping`` for Pods running on the node that just restarted.

Example: Severity-Based Silencing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Silence alerts below a certain severity threshold:

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - severity_silencer:
         severity: LOW  # silence all LOW severity alerts

Example: Name-Based Silencing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Silence specific alerts by name pattern:

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - name_silencer:
         names:
         - "Watchdog"
         - "InfoInhibitor"

Example: Pod Status Silencing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Silence alerts for pods in specific states.

Exclude pods in certain states (stop processing if pod is in these states):

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - pod_status_silencer:
         exclude:
         - "Pending"
         - "ContainerCreating"

Or include only certain states (stop processing unless pod is in these states):

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - pod_status_silencer:
         include:
         - "Running"

Available Silencer Actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

View the complete reference for all silencer actions and their parameters:

* :ref:`node_restart_silencer <node_restart_silencer>` - Silence alerts during node restarts
* :ref:`severity_silencer <severity_silencer>` - Filter alerts by severity level
* :ref:`name_silencer <name_silencer>` - Silence specific alerts by name
* :ref:`silence_alert <silence_alert>` - General-purpose silencing mechanism
* :ref:`pod_status_silencer <pod_status_silencer>` - Silence alerts for pods in specific states

See the full :ref:`Prometheus Silencers <Prometheus Silencers>` reference for detailed documentation on each action.
