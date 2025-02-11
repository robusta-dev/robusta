Remediate using Kubernetes Jobs
######################################

Robusta can run a Kubernetes Job to remediate any Prometheus Alert. In this example we'll remediate a Prometheus alert named ``TestAlert`` by running a Kubernetes job in response.

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

Then, apply the Helm values with a :ref:`Helm Upgrade <Simple Upgrade>`.

Trigger the newly added playbook by simulating a Prometheus alert.

.. code-block:: bash

    robusta playbooks trigger prometheus_alert alert_name=TestAlert


Reference Alert Metadata in Remediation Jobs
-------------------------------------------

When remediating based on alerts, you can access all the alert metadata like name, namespace, cluster name, pod, node and more as environment variables.


Implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this example we are referencing the alert name and a label called region as environment variables in the remediation job. 


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

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

.. note::

    * Alert labels are added as environment variables in the following format ``ALERT_LABEL_{LABEL_NAME}``. For example a label named ``foo`` becomes ``ALERT_LABEL_FOO``


Mount Sensitve Values in Remediation Jobs
-------------------------------------------

Sometimes you might want to reference sensite values like API keys in your remediation jobs. In such cases, Robusta lets you add them as a Kubernetes secret and reference them as environment variables.

Implementation
^^^^^^^^^^^^^^^^^

Let's see how to mount a Kubernetes secret, that can be used in the remediation command:

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

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

.. note::

    * Alert labels are added as environment variables in the following format ``ALERT_LABEL_{LABEL_NAME}``. For example a label named ``foo`` becomes ``ALERT_LABEL_FOO``

