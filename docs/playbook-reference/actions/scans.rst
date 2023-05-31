Scans
########

Robusta includes built-in actions to scan and get insights on Kubernetes clusters.

These actions can be triggered:

* Automatically, on a schedule.
* On demand, via the Robusta UI.
* On demand, via :ref:`cli command <Manual Triggers>`.

KRR - Prometheus-based Kubernetes Resource Recommendations
---------------------------------------------

Robustas `KRR <https://github.com/robusta-dev/krr>`_ is a CLI tool for optimizing resource allocation in Kubernetes clusters.
It gathers pod usage data from Prometheus and recommends requests and limits for CPU and memory.
This reduces costs and improves performance.
By default, every instance of Robusta that's connected to the UI will run a KRR scan on startup. Further KRR scans can be triggered in the UI, and all scans can be viewed there.

With or without the UI, you can configure additional scans on a :ref:`schedule <Scheduled>`.
The results can be sent as a PDF to Slack or to the Robusta UI.

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To set custom tolerations or a nodeSelector update your ``generated_values.yaml`` file as follows:

.. code-block:: yaml
    :name: cb-krr-set-custom-taints

    global_config:
      krr_job_spec:
        tolerations:
        - key: "key1"
          operator: "Exists"
          effect: "NoSchedule"
        nodeSelector:
          nodeName: "your-selector"

Popeye - A Kubernetes Cluster Sanitizer
---------------------------------------------

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To set custom tolerations or a nodeSelector update your ``generated_values.yaml`` file as follows:

.. code-block:: yaml
    :name: cb-popeye-set-custom-taints

    global_config:
      popeye_job_spec:
        tolerations:
        - key: "key1"
          operator: "Exists"
          effect: "NoSchedule"
        nodeSelector:
          nodeName: "your-selector"

Troubleshooting Popeye
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Popeye scans run as Jobs in your cluster. If there are issues with a scan, troubleshoot as follows:

* To find errors with the Popeye job run:

.. code-block:: bash
    :name: cb-popeye-get-events

    kubectl get events --all-namespaces --field-selector=type!=Normal | grep popeye-job

* Additional errors can sometimes be found in the Robusta runner logs:

.. code-block:: bash
    :name: cb-popeye-get-logs

    robusta logs
