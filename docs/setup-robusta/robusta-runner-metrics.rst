Self-Monitoring
======================================

Robusta Metrics Graphs
**************************

Robusta runner supports Prometheus and exposes performance and error metrics on the `/metrics` endpoint.

After Prometheus discovers the ServiceMonitor, the robusta-runner page in the UI will automatically include graphs as shown below.

.. image:: /images/robusta-metrics.png
  :align: center

This guide will help you setup Robusta to observe the collected monitoring data on the Robusta platform.

Exposing Robusta metrics endpoint
***********************************

Once Robusta is running, port forward to its pod using

.. code-block:: bash

  kubectl port-forward deployment/robusta-runner 5000

run

.. code-block:: bash

  curl -s localhost:5000/metrics

The response will look similar to the following snippet, and include the metrics:

.. code-block:: yaml

  # HELP discovery_errors_total Number of discovery process failures.
  # TYPE discovery_errors_total counter
  discovery_errors_total 0.0
  # HELP discovery_errors_created Number of discovery process failures.
  # TYPE discovery_errors_created gauge
  discovery_errors_created 1.6925408357619166e+09
  # HELP discovery_process_time Total discovery process time (seconds)
  # TYPE discovery_process_time summary
  discovery_process_time_count 258.0
  discovery_process_time_sum 87.89608378204866
  # HELP discovery_process_time_created Total discovery process time (seconds)
  # TYPE discovery_process_time_created gauge
  discovery_process_time_created 1.6925408357619708e+09
  # HELP playbooks_errors_total Number of playbooks failures.
  # TYPE playbooks_errors_total counter
  # HELP playbooks_process_time Total playbooks process time (seconds)
  # TYPE playbooks_process_time summary
  playbooks_process_time_count{source=""} 2218.0
  playbooks_process_time_sum{source=""} 215.01851963996887
  playbooks_process_time_count{source="manual_action"} 22.0
  playbooks_process_time_sum{source="manual_action"} 2.7707679271698
  # HELP playbooks_process_time_created Total playbooks process time (seconds)
  # TYPE playbooks_process_time_created gauge
  playbooks_process_time_created{source=""} 1.692540846287054e+09
  playbooks_process_time_created{source="manual_action"} 1.6926052244569693e+09
  # HELP queue_event_total Number of queue events status
  # TYPE queue_event_total counter
  queue_event_total{queue_name="api_server_queue",status="queued"} 1554.0
  queue_event_total{queue_name="api_server_queue",status="processed"} 1554.0
  queue_event_total{queue_name="alerts_queue",status="queued"} 169.0
  queue_event_total{queue_name="alerts_queue",status="processed"} 169.0
  # HELP queue_event_created Number of queue events status
  # TYPE queue_event_created gauge
  queue_event_created{queue_name="api_server_queue",status="queued"} 1.6925408454740999e+09
  queue_event_created{queue_name="api_server_queue",status="processed"} 1.6925408467937994e+09
  queue_event_created{queue_name="alerts_queue",status="queued"} 1.6925409958650925e+09
  queue_event_created{queue_name="alerts_queue",status="processed"} 1.6925409967573514e+09
  # HELP queue_process_time queue process time (seconds)
  # TYPE queue_process_time summary
  queue_process_time_count{queue_name="api_server_queue"} 1554.0
  queue_process_time_sum{queue_name="api_server_queue"} 628.65576171875
  queue_process_time_count{queue_name="alerts_queue"} 169.0
  queue_process_time_sum{queue_name="alerts_queue"} 10279.701471090317
  # HELP queue_size Current size of the queue
  # TYPE queue_size gauge
  queue_size{queue_name="api_server_queue"} 0.0
  queue_size{queue_name="alerts_queue"} 0.0
  ...

Configuring Prometheus monitoring
*************************************

First, verify the discovered by your Prometheus, run:

.. code-block:: bash

  kubectl get prometheus -o yaml | grep -A3 serviceMonitorSelector

The response will look similar to this

.. code-block:: bash

    serviceMonitorSelector:
    matchLabels:
      release: robusta # this label must exists on ServiceMonitors in order to be discovered.
  shards: 1

Robusta helm installation will deploy the following ServiceMonitor CRD into your cluster:

.. Note::

    The ServiceMonitor CRD definition must exists on the cluster.

.. code-block:: yaml

  apiVersion: monitoring.coreos.com/v1
  kind: ServiceMonitor
  metadata:
    name: robusta-runner-service-monitor
    labels:
      # Adjust this label to your Prometheus matchLabels selector
      release: robusta
  spec:
    endpoints:
      - path: /metrics
        port: http
    selector:
      matchLabels:
        app: robusta-runner
    targetLabels:
      - target

Adjust the Robusta ServiceMontior labels so they match the Prometheus CRD.

Now the metrics graph should be visible on the Robusta UI.
