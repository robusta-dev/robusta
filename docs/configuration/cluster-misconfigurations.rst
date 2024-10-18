Kubernetes Misconfigurations (Popeye)
************************************************

`Popeye <https://github.com/derailed/popeye>`_ is a utility that scans live Kubernetes clusters and reports potential issues with resources and configurations.

By optionally integrating Popeye with Robusta you can:

1. Get weekly Popeye scan reports in Slack via Robusta OSS (disabled by default, see below to configure)
2. View Popeye scans from all your clusters in the Robusta UI (enabled by default for UI users)

Sending Weekly Popeye Scan Reports to Slack
===========================================
With or without the UI, you can configure additional scans on a :ref:`schedule <Scheduled>` as shown below. The results can be sent as a PDF to Slack or to the Robusta UI.


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

Taints, Tolerations and NodeSelectors
============================================

To run Popeye on a GPU enabled cluster or on specific nodes you can set custom tolerations or a nodeSelector in your ``generated_values.yaml`` file as follows:

.. code-block:: yaml
    :name: cb-popeye-set-custom-taints

    globalConfig:
      popeye_job_spec:
        tolerations:
        - key: "key1"
          operator: "Exists"
          effect: "NoSchedule"
        nodeSelector:
          kubernetes.io/arch: "amd64"
          nodeName: "your-selector"

.. Note::

    Popeye does `not support <https://github.com/derailed/popeye/issues/253>`_ arm nodes yet. If your cluster has both Arm and x64 nodes add ``kubernetes.io/arch: "amd64"`` as a node selector to schedule Popeye jobs on the x64 nodes.

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

Reference
======================================
.. robusta-action:: playbooks.robusta_playbooks.popeye.popeye_scan
    :recommended-trigger: on_schedule
    You can trigger a Popeye scan at any time, by running the following command:

    .. code-block:: bash

        robusta playbooks trigger popeye_scan
