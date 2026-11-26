Remediate Using Bash Commands
===============================================

Prometheus Alerts can be remediated by running bash commands on existing pods.


Run Bash Command on a Kubernetes Pod
***************************************

To run a command inside existing pods (the pod is chosen according to alert metadata) add the following to your Helm values file:

.. code-block:: yaml

    commandActions:
    - pod_bash_enricher

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: SomeAlert
      actions:
      - pod_bash_enricher:
          bash_command: ls -l /etc/data/db

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.
