Scans
########

Robusta includes built-in actions to scan and get insights on Kubernetes clusters.

These actions can be triggered:

* Automatically, on a schedule.
* On demand, via the Robusta UI.
* On demand, via :ref:`cli command <Manual Triggers>`.

Popeye - A Kubernetes Cluster Sanitizer
---------------------------------------------

`Popeye <https://github.com/derailed/popeye>`_ is a utility that scans live Kubernetes clusters and reports potential issues with resources and configurations.
By default, every instance of Robusta that's connected to the UI will run a Popeye scan on startup. Further Popeye scans can be triggered in the UI, and all scans can be viewed there.

With or without the UI, you can configure additional scans on a :ref:`schedule <Scheduled>`.

.. code-block:: yaml
    :name: cb-popeye-set-periodic-scan

    customPlaybooks:
    - triggers:
    - on_schedule:
        fixed_delay_repeat:
            repeat: 1 # number of times to run or -1 to run forever
            seconds_delay: 604800 # 1 week
    actions:
    - popeye_scan: {}
    sinks:
        - "robusta_ui_sink"

The results can be sent as a PDF to Slack,

.. image:: /images/popeye_slack_example.png
    :width: 1000
    :align: center

or to the Robusta UI.

.. image:: /images/popeye_example.png
    :width: 1000
    :align: center

Other sinks like MSTeams are not supported yet.

.. robusta-action:: playbooks.robusta_playbooks.popeye.popeye_scan on_schedule

    You can trigger a Popeye scan at any time, by running the following command:

    .. code-block:: bash

        robusta playbooks trigger popeye_scan

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
