Scans
########

Robusta includes built-in actions to scan and get insights on Kubernetes clusters.

These actions can be triggered automatically on a schedule, manually using the Robusta Platform and :ref:`manually using the robusta cli <Manual Triggers>`.


Popeye - A Kubernetes Cluster Sanitizer
---------------------------------------------

`Popeye <https://github.com/derailed/popeye>`_ is a utility that scans live Kubernetes cluster and reports potential issues with deployed resources and configurations. by default Robusta will run a Popeye scan on startup.

Popeye scans can be triggerd and viewed in the Robusta platform

.. image:: /images/popeye_example.png
    :width: 1000
    :align: center

.. robusta-action:: playbooks.robusta_playbooks.popeye.popeye_scan

    Manually trigger with:

    .. code-block:: bash

        robusta playbooks trigger popeye_scan

Troubleshooting Popeye
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When triggering a Popeye scan, Popeye will run as a one-off job directly in your cluster.
Use these steps to find possible issues with the scan action.

| Currently Popeye scans are only supported with the Robusta platform and Slack :ref:`sinks <Sinks Reference>`.

* To find errors with the Popeye job run:

.. code-block:: bash
    :name: cb-popeye-get-events

    kubectl get events --all-namespaces --field-selector=type!=Normal | grep popeye-job

* Useful information could be found in the Robusta runner logs, use Robusta CLI:

.. code-block:: bash
    :name: cb-popeye-get-logs

    robusta logs
