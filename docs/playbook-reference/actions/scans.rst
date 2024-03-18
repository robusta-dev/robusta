Scans
########

Robusta includes built-in actions to scan and get insights on Kubernetes clusters.

These actions can be triggered:

* Automatically, on a schedule.
* On demand, via the Robusta UI.
* On demand, via :ref:`cli command <Manual Triggers>`.

KRR - Prometheus-based Kubernetes Resource Recommendations
************************************************************

Robustas `KRR <https://github.com/robusta-dev/krr>`_ is a CLI tool for optimizing resource allocation in Kubernetes clusters.
It gathers pod usage data from Prometheus and recommends requests and limits for CPU and memory.
This reduces costs and improves performance.
By default, every instance of Robusta that's connected to the UI will run a KRR scan on startup. Further KRR scans can be triggered in the UI, and all scans can be viewed there.

With or without the UI, you can configure additional scans on a :ref:`schedule <Scheduled>`.
The results can be sent as a PDF to Slack or to the Robusta UI.

.. grid:: 1 1 1 1

    .. grid-item::

        .. md-tab-set::

            .. md-tab-item:: Slack

                .. image:: /images/krr_slack_example.png
                    :width: 1000px

            .. md-tab-item:: Robusta UI

                .. image:: /images/krr_example.png
                    :width: 1000px


.. robusta-action:: playbooks.robusta_playbooks.krr.krr_scan on_schedule

    You can trigger a KRR scan at any time, by running the following command:

    .. code-block:: bash

        robusta playbooks trigger krr_scan


Taints, Tolerations and NodeSelectors
============================================

To set custom tolerations or a nodeSelector update your ``generated_values.yaml`` file as follows:

.. code-block:: yaml
    :name: cb-krr-set-custom-taints

    globalConfig:
      krr_job_spec:
        tolerations:
        - key: "key1"
          operator: "Exists"
          effect: "NoSchedule"
        nodeSelector:
          nodeName: "your-selector"

Customizing Efficiency Recommendations in the Robusta UI
====================================================================================
You can tweak KRR's recommendation algorithm to suit your environment using the ``krr_args`` setting in Robusta's Helm chart.

Add the following config to the top of your ``generated_values.yaml`` with your custom values. KRR will use these values every time it sends data to the Robusta UI or other destinations.

If you are having performance issues, specifically with Prometheus using a lot of memory, reduce ``max_workers`` to reduce memory usage. KRR uses 3 workers by default.

.. code-block:: yaml

    globalConfig:
      krr_args: "--cpu-min 15 --mem-min 200 --cpu_percentile 90 --memory_buffer_percentage 25 --max-workers 40"
      max_workers: 2 

**Common KRR Settings**

.. list-table::
   :widths: 25 10 40 25
   :header-rows: 1

   * - ``Argument``
     - Type
     - Used for
     - Default value
   * - ``--cpu-min``
     - INTEGER
     - Sets the minimum recommended CPU value in millicores.
     - 10
   * - ``--mem-min``
     - INTEGER
     - Sets the minimum recommended memory value in MB.
     - 100
   * - ``--history_duration``
     - TEXT
     - The duration of the history data to use (in hours).
     - 336
   * - ``--timeframe_duration``
     - TEXT
     - The step for the history data (in minutes).
     - 1.25
   * - ``--cpu_percentile``
     - TEXT
     - The percentile to use for the CPU recommendation.
     - 99
   * - ``--memory_buffer_percentage``
     - TEXT
     - The percentage of added buffer to the peak memory usage for memory recommendation.
     - 15
   * - ``--points_required``
     - TEXT
     - The number of data points required to make a recommendation for a resource.
     - 100



Popeye - A Kubernetes Cluster Sanitizer
************************************************

`Popeye <https://github.com/derailed/popeye>`_ is a utility that scans live Kubernetes clusters and reports potential issues with resources and configurations.
By default, every instance of Robusta that's connected to the UI will run a Popeye scan on startup. Further Popeye scans can be triggered in the UI, and all scans can be viewed there.

With or without the UI, you can configure additional scans on a :ref:`schedule <Scheduled>` as shown below.

.. code-block:: yaml
    :name: cb-popeye-set-periodic-scan

    customPlaybooks:
    - triggers:
      - on_schedule:
          fixed_delay_repeat:
            repeat: 1 # number of times to run or -1 to run forever
            seconds_delay: 604800 # 1 week
      actions:
      - popeye_scan:
          spinach: |
            popeye:
              excludes:
                  v1/pods:
                  - name: rx:kube-system
      sinks:
      - "robusta_ui_sink"

The results can be sent as a PDF to Slack or to the Robusta UI.

.. grid:: 1 1 1 1

    .. grid-item::

        .. md-tab-set::

            .. md-tab-item:: Slack

                .. image:: /images/popeye_slack_example.png
                    :width: 1000px

            .. md-tab-item:: Robusta UI

                .. image:: /images/popeye_example.png
                    :width: 1000px


.. Note::

    Other sinks like MSTeams are not supported yet.

.. robusta-action:: playbooks.robusta_playbooks.popeye.popeye_scan on_schedule

    You can trigger a Popeye scan at any time, by running the following command:

    .. code-block:: bash

        robusta playbooks trigger popeye_scan

Taints, Tolerations and NodeSelectors
============================================

To set custom tolerations or a nodeSelector update your ``generated_values.yaml`` file as follows:

.. code-block:: yaml
    :name: cb-popeye-set-custom-taints

    globalConfig:
      popeye_job_spec:
        tolerations:
        - key: "key1"
          operator: "Exists"
          effect: "NoSchedule"
        nodeSelector:
          nodeName: "your-selector"

Troubleshooting Popeye
=======================

Popeye scans run as Jobs in your cluster. If there are issues with a scan, troubleshoot as follows:

Events
---------------------
* To find errors with the Popeye job run:

.. code-block:: bash
    :name: cb-popeye-get-events

    kubectl get events --all-namespaces --field-selector=type!=Normal | grep popeye-job

Logs
---------------------
* Additional errors can sometimes be found in the Robusta runner logs:

.. code-block:: bash
    :name: cb-popeye-get-logs

    robusta logs


Known issues
---------------------

``couldn't get resource list for external.metrics.k8s.io/v1beta1``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a known issue, there is a working workaround, which involves deploying a dummy workload.
Read more about it `here <https://github.com/kedacore/keda/issues/4224#issuecomment-1426749781>`_.

``exec /bin/sh: exec format error``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

At the moment, Popeye docker images are only compiled for linux/amd64 os/arch.
This error suggests you are running the Popeye image on a different os/arch node.
