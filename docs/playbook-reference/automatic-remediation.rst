Automatic Remediation
===============================

Robusta can automatically remediate Prometheus Alerts by running Kubernetes Jobs, or by running bash commands on existing nodes or pods.

Lets look at some examples.

Running a Kubernetes Job to Remediate a Prometheus Alert
**********************************************************

In this example we'll remediate a Prometheus alert named ``TestAlert`` by running a Kubernetes job in response.

Add the following to your Helm values, under the :ref:`customPlaybooks<customPlaybooks>` value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        # this trigger section defines when to run the remediation
        - on_prometheus_alert:
            alert_name: TestAlert
    
      actions:
        # this actions section defines what to do when the trigger fires
        - alert_handling_job:
            command:
              - sh
              - -c
              - echo "placeholder for taking an action that fixes the alert"
            image: busybox
            notify: true
            wait_for_completion: true
            completion_timeout: 100

To test this playbook, apply the Helm values with a :ref:`Helm Upgrade <Simple Upgrade>`. Then trigger this playbook by simulating a Prometheus alert:

.. code-block:: bash

    robusta playbooks trigger prometheus_alert alert_name=TestAlert

Refering to Alert Metadata in Remediation Jobs
**********************************************************

Here we reference alert labels in the remediation command:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_prometheus_alert:
            alert_name: TestAlert
      actions:
        - alert_handling_job:
            # you can access information from the alert using environment variables
            command:
              - sh
              - -c
              - echo \"$ALERT_NAME $ALERT_LABEL_REGION dumping all available environment variables, which include alert metadata and labels\" && env && sleep 60
            image: busybox
            notify: true
            wait_for_completion: true
            completion_timeout: 100
            env:
              - name: GITHUB_SECRET
                valueFrom:
                  secretKeyRef:
                    name: robusta-github-key
                    key: githubapikey

.. note::

    * Alert labels are added as environment variables in the following format ``ALERT_LABEL_{LABEL_NAME}``. For example a label named ``foo`` becomes ``ALERT_LABEL_FOO``


Mounting Kubernetes Secrets in Remediation Jobs
************************************************************

Lets see how to mount a Kubernetes secret, that can be used in the remediation command:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_prometheus_alert:
            alert_name: TestAlert
      actions:
        - alert_handling_job:
            # you can access mounted secrets here from the alert using environment variables
            command:
              - sh
              - -c
              - echo \"$GITHUB_SECRET\"
            image: busybox
            notify: true
            wait_for_completion: true
            completion_timeout: 100
            env:
              - name: GITHUB_SECRET
                valueFrom:
                  secretKeyRef:
                    name: robusta-github-key
                    key: githubapikey

.. note::

    * Alert labels are added as environment variables in the following format ``ALERT_LABEL_{LABEL_NAME}``. For example a label named ``foo`` becomes ``ALERT_LABEL_FOO``


Running Bash Commands for Alert Remediation
********************************************

Alerts can be remediated by running bash commands on existing nodes or pods.

To run a command on a Kubernetes node (the node is chosen according to alert metadata):

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: SomeAlert
      actions:
      - node_bash_enricher:
          bash_command: do something
  
To run a command inside existing pods (the pod is chosen according to alert metadata):

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: SomeAlert
      actions:
      - pod_bash_enricher:
          bash_command: ls -l /etc/data/db


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
