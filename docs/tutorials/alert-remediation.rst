Remediate Prometheus Alerts
===============================

Robusta can respond to Prometheus alerts and automatically remediate them.

Using Kubernetes Jobs for Alert Remediation
***********************************************

A popular remediation method involves running Kubernetes Jobs when alerts fire.

Add the following to your :ref:`customPlaybooks<customPlaybooks>`:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: SomeAlert
      actions:
      - alert_handling_job:
          command:
          - "echo"
          - "do something to fix it"
          image: "a_docker_image"

Perform a :ref:`Helm Upgrade <Simple Upgrade>`.

Test this playbook by simulating a Prometheus alert:

.. code-block:: bash

    robusta playbooks trigger prometheus_alert alert_name=SomeAlert

Running Bash Commands for Alert Remediation
********************************************

Alerts can also be remediated with bash commands:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: SomeAlert
      actions:
      - node_bash_enricher:
         bash_command: do something

Further Reading
*****************

* Reference for the :ref:`alert_handling_job<alert_handling_job>` action
* Reference for the :ref:`node_bash_enricher<node_bash_enricher>` action
* :ref:`More remediation actions <Remediation>`

..     .. tab-item:: Remediate alerts

..         .. admonition:: Temporarily increase the HPA maximum so you can go back to sleep

..             .. image:: /images/alert_on_hpa_reached_limit1.png
..                 :width: 600
..                 :align: center
