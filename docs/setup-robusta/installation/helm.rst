Install with Helm
#################

This guide installs the Robusta runner with Helm and sends its notifications to a Slack channel.

Prerequisites
-------------

* A Kubernetes cluster
* Helm
* A Slack API key and channel. See :ref:`Creating Custom Slack Apps`.

Add the Helm repository
-----------------------

.. code-block:: bash

    helm repo add robusta https://robusta-charts.storage.googleapis.com
    helm repo update

Write a values file
-------------------

The chart needs at least one sink. Save the following as ``generated_values.yaml``:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: main_slack_sink
        api_key: <YOUR_SLACK_API_KEY>
        slack_channel: <YOUR_SLACK_CHANNEL>

To keep the Slack key out of this file, see :ref:`Managing Secrets`. For other destinations, see :doc:`/notification-routing/configuring-sinks`.

Install
-------

.. code-block:: bash

    helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

``clusterName`` is required.

Verify that Robusta is running and there are no errors in the logs:

.. code-block:: bash

    kubectl logs -n <NAMESPACE> -l app=robusta-runner

Keep ``generated_values.yaml``: you pass it again on every :ref:`upgrade <Simple Upgrade>`.

Next, send Prometheus alerts to Robusta: see :doc:`/configuration/index`.
