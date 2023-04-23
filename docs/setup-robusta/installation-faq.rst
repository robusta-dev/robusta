Troubleshooting and FAQ
################################

robusta-runner isn't working or has exceptions
================================================
Try checking the pod's memory consumption and if necessary increasing the memory request in the Helm values:

.. code-block:: yaml

    runner:
      resources:
        requests:
          memory: 2048Mi
        limits:
          memory: 2048Mi

Here's a representative error caused by too little memory:

.. code-block::

    2023-04-17 23:37:43.019 ERROR    Discovery process internal error
    2023-04-17 23:37:43.022 INFO     Initialized new discovery pool
    2023-04-17 23:37:43.022 ERROR    Failed to run publish discovery for robusta_ui_sink
    Traceback (most recent call last):
      File "/app/src/robusta/core/sinks/robusta/robusta_sink.py", line 175, in __discover_resources
        results: DiscoveryResults = Discovery.discover_resources()
      File "/app/src/robusta/core/discovery/discovery.py", line 288, in discover_resources
        raise e
      File "/app/src/robusta/core/discovery/discovery.py", line 280, in discover_resources
        return future.result()
      File "/usr/local/lib/python3.9/concurrent/futures/_base.py", line 446, in result
        return self.__get_result()
      File "/usr/local/lib/python3.9/concurrent/futures/_base.py", line 391, in __get_result
        raise self._exception
    concurrent.futures.process.BrokenProcessPool: A process in the process pool was terminated abruptly while the future was running or pending.


Can I install without the Robusta cli?
========================================
Yes, using the cli is optional. It auto-generates helm values, but you can also handwrite them:

1. Fetch Robusta's default **Helm values**:

.. code-block:: bash
    :name: cb-helm-repo-add-show-values

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
    helm show values robusta/robusta

2. Modify those values to your heart's content. (See our :ref:`Configuration Guide`.)

3. Do a ``helm install``.

The helm chart in GitHub doesn't work. Why?
========================================================
It has certain placeholders. For example, ``runner.image`` is set during our release workflow.

Use our Helm repository instead of our GitHub repository. See above.

Can I install Robusta in a different namespace?
================================================

Yes. By default Robusta is installed in the ``default`` namespace but you can change that.

For example, to install in the ``robusta`` namespace:

.. code-block:: bash
    :name: cb-helm-install-robusta-custom

    helm install robusta robusta/robusta -f ./generated_values.yaml -n robusta --create-namespace --set clusterName=<YOUR_CLUSTER_NAME>

Verify success by checking that two Robusta pods are running:

.. code-block:: bash
   :name: cb-get-pods-robusta-logs-custom

    kubectl get pods -n robusta

.. warning::

    Make sure you add the ``--namespace`` flag to future ``robusta`` cli commands.

Does Robusta support Thanos/Cortex/Mimir/VictoriaMetrics?
============================================================
Any Prometheus-compatible solution is fine. Just follow instructions under :ref:`Integrate with Existing Prometheus`

Can I use Robusta with DataDog?
============================================================
Yes, we have a DataDog integration available. Try it out.

Is NewRelic supported?
=======================
It's being planned, speak to us on Slack.

Does Robusta replace monitoring tools?
============================================================
Robusta's :ref:`all-in-one package <Monitor Kubernetes from Scratch>` is a complete monitoring and observability solution.

Alternatively, you can keep your existing tools and add-on robusta.
