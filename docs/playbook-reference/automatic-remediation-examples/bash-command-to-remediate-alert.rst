Remediate Using Bash Commands
===============================================

Prometheus Alerts can be remediated by running bash commands on existing nodes or pods.


Run Bash Command on a Kubernetes node
***************************************

To run a command on a Kubernetes node (the node is chosen according to alert metadata) add the following to your Helm values file:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: SomeAlert
      actions:
      - node_bash_enricher:
          bash_command: do something
  
Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Run Bash Command on a Kubernetes Pod
***************************************

To run a command inside existing pods (the pod is chosen according to alert metadata) add the following to your Helm values file:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: SomeAlert
      actions:
      - pod_bash_enricher:
          bash_command: ls -l /etc/data/db

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.
