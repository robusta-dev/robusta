List of built-in playbooks
############################

Application Visibility and Troubleshooting
-------------------------------------------

add_deployment_lines_to_grafana
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
| **What it does:** add annotations to grafana showing new versions of your application
| **When it runs:** when the image tags inside a deployment change
| **Enabling it:**

.. code-block:: yaml

   active_playbooks
     - name: "add_deployment_lines_to_grafana"
       action_params:
         grafana_dashboard_uid: "uid_from_url"
         grafana_api_key: "grafana_api_key_with_editor_role"
         grafana_url: "https://mygrafana.mycompany.com"

| **The results:**

.. image:: /images/grafana-deployment-enrichment.png
  :width: 400
  :align: center

.. tip::
    The ``grafana_url`` parameter can usually be left blank for a Grafana running in the same cluster which will be automatically detected.

add_alert_lines_to_grafana
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
| **What it does:** add annotations to grafana showing Prometheus alerts
| **When it runs:** when a relevant Prometheus alert is triggered
| **Enabling it:**

.. code-block:: yaml

    active_playbooks:
      - name: "add_alert_lines_to_grafana"
        action_params:
          grafana_api_key: "grafana_api_key_with_editor_role"
          grafana_url: "http://grafana-service-name.namespace.svc"
          annotations:
            - alert_name: "CPUThrottlingHigh"
              dashboard_uid: "09ec8aa1e996d6ffcd6817bbaff4db1b" # copy this from the dashboard's URL
            - alert_name: "TargetDown"
              dashboard_uid: "other_uid_goes_here"
              dashboard_panel: "ErrorBudget"                    # only add annotations to one panel on the dashboard

| **The resuls:**

.. image:: /images/add-alert-lines-to-grafana.png
  :width: 400
  :align: center

.. tip::
    The ``grafana_url`` parameter can usually be left blank for a Grafana running in the same cluster which will be automatically detected.

    The ``dashboard_panel`` is an optional parameter. When present, annotations will be added only to panels containing that text in their title.

git_change_audit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
| **What it does:** syncs Kubernetes resources from the cluster to git as yaml files (cluster/namespace/resources hierarchy)
| **When it runs:** when a configuration spec changes in the cluster
| **Enabling it:**

.. code-block:: yaml

  - name: "git_change_audit"
    action_params:
      cluster_name: "robusta-demo"
      git_url: "git@github.com/robusta/robusta-audit.git"
      git_key: |
        -----BEGIN OPENSSH PRIVATE KEY-----
        YOUR PRIVATE KEY DATA
        -----END OPENSSH PRIVATE KEY-----
      ignored_changes:
      - "replicas"

| **cluster_name:** Used as the root directory in the repo. should be different, for different Kubernetes clusters
| **git_url:** url to a github repository
| **git_key:** github deployment key on the audit repository, with **Allow write access**. To set this up `Generate <https://docs.github.com/en/developers/overview/managing-deploy-keys#setup-2>`_ your private/public keys pair.
| Store the public key as github deployment key on the audit repository, and the private key data in the playbook configuration.

| **Note:** The ``ignored_changes`` is an optional parameter, used to filter out irrelevant changes.
| In the example above, we filter out ``spec.replicas`` changes, so that HPA changes won't appear as spec changes
| In order to filter out ``spec.field_name`` add ``field_name`` to the ``ignored_changes`` array

| **The results:**

.. image:: /images/git-audit.png
  :width: 1200
  :align: center

restart_loop_reporter
^^^^^^^^^^^^^^^^^^^^^
| **What it does:** send a crashing pod's logs to slack
| **When it runs:** when a pod crashes. (can be limited to a specific reason) .
| **Enabling it:**

.. code-block:: yaml

   active_playbooks:
     - name: "restart_loop_reporter"
       action_params:
         rate_limit: 7200 # seconds
         restart_reason: "CrashLoopBackOff"

| Note: Both restart_reason (default to None) and rate_limit (default to 3600 seconds) are optional parameters.

| **The results:**

.. image:: /images/restart-loop-reporter.png
  :width: 600
  :align: center

python_profiler
^^^^^^^^^^^^^^^
| **What it does:** run a CPU profiler on any python pod for 60 seconds and send the result to Slack.
| **When it runs:** when you trigger it manually with a command like:

.. code-block:: bash

   robusta playbooks trigger python_profiler pod_name=your-pod namespace=you-ns process_name=your-process seconds=5

| **Parameters:** see below. All parameters are optional except for ``pod_name`` and ``namespace``. ``pod_name`` can be the prefix of the pod name and doesn't need to be a full match.

| **Enabling it:** add to active_playbooks.yaml before manually trigger using the Robusta CLI (as described above):

.. code-block:: yaml

   active_playbooks:
     - name: "python_profiler"

| **The results:**

.. image:: /images/python-profiler.png
  :width: 600
  :align: center

pod_ps
^^^^^^
| **What it does:** gets a list of processes inside any pod prints the result in the terminal
| **When it runs:** manually triggered.

Stress Testing and Chaos Engineering
------------------------------------

generate_high_cpu
^^^^^^^^^^^^^^^^^^
| **What it does:** cause high CPU usage in the cluster
| **When it runs:** manually triggered.

http_stress_test
^^^^^^^^^^^^^^^^^
| **What it does:** creates many http requests for a given url
| **When it runs:** when you trigger it manually with a command like:

.. code-block:: bash

   robusta playbooks trigger http_stress_test url=http://grafana.default.svc:3000 n=1000

| **Enabling it:** add to active_playbooks.yaml before manually trigger using the Robusta CLI (as described above):

.. code-block:: yaml

   active_playbooks:
     - name: "http_stress_test"

| **The results:**

.. image:: /images/http-stress-test.png
  :width: 600
  :align: center


Kubernetes Monitoring
---------------------

incluster_ping
^^^^^^^^^^^^^^^^^
| **What it does:** pings a hostname from within the cluster
| **When it runs:** when you trigger it manually with a command like:

.. code-block:: bash

   robusta playbooks trigger incluster_ping hostname=grafana.default.svc

| **Enabling it:** add to active_playbooks.yaml before manually trigger using the Robusta CLI (as described above):

.. code-block:: yaml

   active_playbooks:
     - name: "incluster_ping"

deployment_babysitter
^^^^^^^^^^^^^^^^^^^^^
| **What it does:** send notifications to Slack describing changes to deployments
| **When it runs:** when deployments are created, modified, and deleted.

Enabling it:

.. code-block:: yaml

   active_playbooks:
     - name: "deployment_babysitter"
       action_params:
         fields_to_monitor: ["spec.replicas"]

.. image:: /images/deployment-babysitter.png
  :width: 600
  :align: center

deployment_status_report
^^^^^^^^^^^^^^^^^^^^^^^^^
| **What it does:** sends a list of grafana panels
| **When it runs:** After a deployment is updated, on configured time intervals

Enabling it:

.. code-block:: yaml

   active_playbooks:
     - name: "deployment_status_report"
       trigger_params:
         name_prefix: "MY_MONITORED_DEPLOYMENT"
       action_params:
         report_name: "MY REPORT NAME"
         on_image_change_only: true  # Default is true, can be omitted.
         delays:
         - 60       # 60 seconds after a deployment change
         - 600      # 10 minutes after the previous run, i.e. 11 minutes after the deployment change
         - 1200     # 31 minutes after the deployment change
         reports_panel_urls:
         - "http://MY_GRAFANA/d-solo/200ac8fdbfbb74b39aff88118e4d1c2c/kubernetes-compute-resources-node-pods?orgId=1&from=now-1h&to=now&panelId=3"
         - "http://MY_GRAFANA/d-solo/SOME_OTHER_DASHBOARD/.../?orgId=1&from=now-1h&to=now&panelId=3"
         - "http://MY_GRAFANA/d-solo/SOME_OTHER_DASHBOARD/.../?orgId=1&from=now-1h&to=now&panelId=3"

.. note::
    * It's highly recommended to put relative time arguments, rather then absolute. i.e. from=now-1h&to=now
    * Configuring no ``name_prefix`` or ``on_image_change_only: false``, may result in too noisy channel

| **The results:**

.. image:: /images/deployment-change-report.png
  :width: 1000
  :align: center

Kubernetes Optimization
-----------------------

config_ab_testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
| **What it does:** Automatically apply different YAML configurations to a Kubernetes resource for a limited period of time so that you can compare their impact. Also adds adds grafana annotations showing when each configuration was applied so that you can easily compare the performance impact of each configuration.
| **When it runs:** every predefined period, defined in the playbook configuration

| Note: Only changing attributes that already exists in the active configuration is supported.(For example, you can change resources.requests.cpu, if that attribute already exists in the deployment)

| Example use cases:

* **Troubleshooting** - Trying to understand what's the first version I see a production bug. I can easily iterate over image tags and find out
* **Cost optimization** - Compare the cost of different deployment configurations to one another by iterating over given configuration sets
* **Performance optimization** - Compare the performance of different deployment configurations to one another by iterating over given configuration sets

Enabling it:

.. code-block:: yaml

   active_playbooks
     - name: "config_ab_testing"
       trigger_params:
         seconds_delay: 1200 # 20 min
       action_params:
         grafana_dashboard_uid: "uid_from_url"
         grafana_api_key: "grafana_api_key_with_editor_role"
         grafana_url: "https://mygrafana.mycompany.com"
         kind: "deployment"
         name: "demo-deployment"
         namespace: "robusta"
         configuration_sets:
         - config_set_name: "low cpu high mem"
           config_items:
             "spec.template.spec.containers[0].resources.requests.cpu": 250m
             "spec.template.spec.containers[0].resources.requests.memory": 128Mi
         - config_set_name: "high cpu low mem"
           config_items:
             "spec.template.spec.containers[0].resources.requests.cpu": 750m
             "spec.template.spec.containers[0].resources.requests.memory": 64Mi

| The results:

.. image:: /images/ab-testing.png
  :width: 400
  :align: center

disk_benchmark
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
| **What it does:** Automatically create a persistent volume (disk) and run disk performance benchmark on a pod using it.
| **When it runs:** when you trigger it manually with a command like:

.. code-block:: bash

   robusta playbooks trigger disk_benchmark storage_class_name=fast disk_size=200Gi test_seconds=60

| **Enabling it:** add to active_playbooks.yaml before manually trigger using the Robusta CLI (as described above):

.. code-block:: yaml

   active_playbooks:
     - name: "disk_benchmark"


| Note: When the benchmark is done, all the resources used for it are deleted.
| Note: storage_class_name should be one of the StorageClasses available on your cluster. You can add storage classes, and use it for the test

| The results:

.. image:: /images/disk-benchmark.png
  :width: 1000
  :align: center


Kubernetes Error Handling
-------------------------

HPA max replicas
^^^^^^^^^^^^^^^^^
| **What it does:** Send a slack notification, and allows to easily increase the HPA max replicas limit
| **When it runs:** When an HPA object reaches the max replicas limit (When desired replicas == max replicas limit)

Enabling it:

.. code-block:: yaml

   active_playbooks
   - name: "alert_on_hpa_reached_limit"
     action_params:
       increase_pct: 20   # Increase factor (%)


| The results:

.. image:: /images/hpa-max-replicas.png
  :width: 600
  :align: center

Alert Enrichment
---------------------
This is a special playbook that has out-of-the box knowledge about specific Prometheus alerts. See :ref:`prometheus-alert-enrichment` for details.