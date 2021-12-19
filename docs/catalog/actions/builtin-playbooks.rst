List of built-in playbooks
############################

.. warning:: This page contains out-of-date information. It is currently being updated to reflect Robusta's new configuration format.

Application Visibility and Troubleshooting
-------------------------------------------

git_change_audit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** syncs Kubernetes resources from the cluster to git as yaml files (cluster/namespace/resources hierarchy)

            **When it runs:** when a configuration spec changes in the cluster

            .. image:: /images/git-audit.png
               :width: 1200
               :align: center

        .. tab-item:: Configuration

            .. code-block:: yaml

              playbooks:
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

            ``cluster_name`` Used as the root directory in the repo. should be different, for different Kubernetes clusters

            ``ignored_changes`` an optional parameter, used to filter out irrelevant changes. In the example above, we filter out changes to `spec.replicas`, so that HPA changes won't appear as spec changes

            ``git_url`` url to a github repository

            ``git_key`` github deployment key on the audit repository, with *allow write access*. To set this up `generate a private/public key pair for GitHub <https://docs.github.com/en/developers/overview/managing-deploy-keys#setup-2>`_.
            Store the public key as the Github deployment key and the private key in the playbook configuration.

argo_app_sync
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** syncs an Argo CD application

            **When it runs:** can be triggered by any event or manually

            .. image:: /images/argo-app-sync.png
               :width: 1200
               :align: center

        .. tab-item:: Configuration

            .. code-block:: yaml

              playbooks:
                - name: "argo_app_sync"
                  action_params:
                    argo_url: "https://my-argo.server.com"
                    argo_token: "ARGO TOKEN"
                    argo_app_name: "my app name"

            ``argo_url`` Argo CD server url

            ``argo_token`` Argo CD authentication token

            ``argo_app_name`` Argo CD application that needs syncing

            Optional:
            ``argo_verify_server_cert`` verify Argo CD server certificate. Defaults to True

            ``rate_limit_seconds`` this playbook is rate limited. Defaults to 1800 seconds.

restart_loop_reporter
^^^^^^^^^^^^^^^^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** send a crashing pod's logs to slack

            **When it runs:** when a pod crashes. (can be limited to a specific reason) .

            .. image:: /images/restart-loop-reporter.png
              :width: 600
              :align: center

        .. tab-item:: Configuration

            .. code-block:: yaml

               playbooks:
                 - name: "restart_loop_reporter"
                   action_params:
                     rate_limit: 3600
                     restart_reason: "CrashLoopBackOff"

            ``restart_reason`` optional parameter, defaults to any reason

            ``rate_limit`` optional parameter, measured in seconds, defaults to 3600

pod_ps
^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** Gets a list of processes inside any pod prints the result in the terminal.

            **When it runs:** Manually triggered.

            **More documentation coming soon**

Stress Testing and Chaos Engineering
------------------------------------

generate_high_cpu
^^^^^^^^^^^^^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** Causes high CPU usage in the cluster.

            **When it runs:** Manually triggered.

            **More documentation coming soon**

http_stress_test
^^^^^^^^^^^^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** Creates many http requests for a given url

            **When it runs:** When you trigger it manually

            .. image:: /images/http-stress-test.png
              :width: 600
              :align: center

        .. tab-item:: Configuration

            .. code-block:: yaml

               playbooks:
                 - name: "http_stress_test"

        .. tab-item:: Manual Trigger

            .. code-block:: bash

               robusta playbooks trigger http_stress_test url=http://grafana.default.svc:3000 n=1000

Kubernetes Monitoring
---------------------

incluster_ping
^^^^^^^^^^^^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** pings a hostname from within the cluster

            **When it runs:** when you trigger it manually with a command like:

        .. tab-item:: Configuration

            .. code-block:: yaml

               playbooks:
                 - name: "incluster_ping"

        .. tab-item:: Manual Trigger

            .. code-block:: bash

               robusta playbooks trigger incluster_ping hostname=grafana.default.svc


resource_babysitter
^^^^^^^^^^^^^^^^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** send notifications to Slack describing changes to deployments

            **When it runs:** when deployments are created, modified, and deleted.

            .. image:: /images/deployment-babysitter.png
              :width: 600
              :align: center
        .. tab-item:: Configuration

            .. code-block:: yaml

               playbooks:
                 - name: "deployment_babysitter"
                   action_params:
                     fields_to_monitor: ["spec.replicas"]


deployment_status_report
^^^^^^^^^^^^^^^^^^^^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** sends screenshots of grafana panels

            **When it runs:** After a deployment is updated, on configured time intervals

            .. image:: /images/deployment-change-report.png
              :width: 1000
              :align: center

        .. tab-item:: Configuration

            .. code-block:: yaml

               playbooks:
                 - name: "deployment_status_report"
                   trigger_params:
                     name_prefix: "MY_MONITORED_DEPLOYMENT"
                   action_params:
                     report_name: "MY REPORT NAME"
                     on_image_change_only: true
                     delays:
                     - 60       # 60 seconds after a deployment change
                     - 600      # 10 minutes after the previous run, i.e. 11 minutes after the deployment change
                     - 1200     # 31 minutes after the deployment change
                     reports_panel_urls:
                     - "http://MY_GRAFANA/d-solo/200ac8fdbfbb74b39aff88118e4d1c2c/kubernetes-compute-resources-node-pods?orgId=1&from=now-1h&to=now&panelId=3"
                     - "http://MY_GRAFANA/d-solo/SOME_OTHER_DASHBOARD/.../?orgId=1&from=now-1h&to=now&panelId=3"
                     - "http://MY_GRAFANA/d-solo/SOME_OTHER_DASHBOARD/.../?orgId=1&from=now-1h&to=now&panelId=3"

            ``reports_panel_urls`` it's highly recommended to put relative time arguments, rather then absolute. i.e. from=now-1h&to=now

            ``on_image_change_only`` default is true, can be omitted.

            Configuring no ``name_prefix`` or ``on_image_change_only: false``, may result in too noisy channel


Kubernetes Optimization
-----------------------

config_ab_testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** Apply YAML configurations to Kubernetes resources for limited periods of time. Adds adds grafana annotations showing when each configuration was applied.

            **When it runs:** every predefined period, defined in the playbook configuration

            **Example use cases:**

            * **Troubleshooting** - Finding the first version a production bug appeared by iterating over image tags

            * **Cost/performance optimization** - Comparing the cost or performance of different deployment configurations

            .. image:: /images/ab-testing.png
              :width: 400
              :align: center

        .. tab-item:: Configuration

            .. code-block:: yaml

               playbooks:
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

            Only changing attributes that already exists in the active configuration is supported.
            For example, you can change resources.requests.cpu, if that attribute already exists in the deployment.

disk_benchmark
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** Automatically create a persistent volume and run a disk performance benchmark with it.

            **When it runs:** When manually triggered

            .. image:: /images/disk-benchmark.png
              :width: 1000
              :align: center

        .. tab-item:: Configuration

            .. code-block:: yaml

               playbooks:
                 - name: "disk_benchmark"

        .. tab-item:: Manual trigger

            .. code-block:: bash

               robusta playbooks trigger disk_benchmark storage_class_name=fast disk_size=200Gi test_seconds=60

            When the benchmark is done, all the resources used for it will be deleted.

            ``storage_class_name`` should be one of the StorageClasses available on your cluster


Kubernetes Error Handling
-------------------------

HPA max replicas
^^^^^^^^^^^^^^^^^

.. admonition:: Playbook

    .. tab-set::

        .. tab-item:: Description

            **What it does:** Send a slack notification and allow increasing the HPA max replicas limit

            **When it runs:** When an HPA object reaches the max replicas limit

            .. image:: /images/hpa-max-replicas.png
              :width: 600
              :align: center

        .. tab-item:: Configuration

            .. code-block:: yaml

               playbooks
               - name: "alert_on_hpa_reached_limit"
                 action_params:
                   increase_pct: 20   # Increase factor (%)

Alert Enrichment
---------------------
This is a special playbook that has out-of-the box knowledge about specific Prometheus alerts. See :ref:`prometheus-alert-enrichment` for details.