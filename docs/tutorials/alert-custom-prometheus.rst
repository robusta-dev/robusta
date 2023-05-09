.. _define-alerts:

Define Custom Prometheus Alerts
##############################################

You can define new alerts in two ways using Robusta:

1. Prometheus Alerts - Using PromQL
2. Robusta Playbooks - Using :ref:`customPlaybooks YAML <What are Playbooks?>`

These methods are not mutually exclusive. Robusta playbooks can respond to Prometheus alerts, or they can generate
alerts themselves by listening directly to the Kubernetes APIServer. To better understand the trade-offs, refer to
:ref:`Should I generate alerts with Robusta or with Prometheus? <robusta-or-prometheus-alerts>`

In this tutorial, we use the first method to generate a custom Prometheus alert using PromQL. In the next tutorial,
we define a custom Robusta playbook that enhances the alert and makes it better.

Prerequisites
--------------

One of the following:

* Robusta's embedded Prometheus Stack
* An external Prometheus integrated with Robusta, including the Prometheus Operator.

Defining a Custom Alert
---------------------------------------

Prometheus Alerts are defined on Kubernetes using the *PrometheusRule CRD*.

.. note:: What is the PrometheusRule CRD?

    CRDs (Custom Resources Definitions) extend Kubernetes API with new resource types. You can apply and edit these
    resources using ``kubectl`` just like Pods, Deployments, and other builtin resources.

    The Prometheus Operator adds CRDs to Kubernetes so you can control Prometheus alerts with ``kubectl``. Whenever you
    apply or edit a ``PrometheusRule`` CRD, the operator will update Prometheus's configuration automatically.

    When Robusta's embedded Prometheus Stack is enabled, the Prometheus Operator is installed automatically.

.. Define a ``PrometheusRule`` to TODO.

.. .. code-block:: yaml

..     TODO

.. Apply this PrometheusRule to your cluster using ``kubectl``:

.. code-block:: bash

    kubectl apply -f test-rule.yaml

Testing the Alert
---------------------------------------

Deploy a broken Pod that will deliberately trigger the Prometheus alert we defined:

.. code-block:: bash

    kubectl apply -f <some example from our demo repo>

By default, Prometheus doesn't send alerts immediately. It waits X seconds to avoid sending flaky alerts that fire
temporarily and then immediately stop.

.. note:: Thresholds vs Events

    Prometheus and Robusta work a little differently. Prometheus alerts based on thresholds and time periods,
    so it has built-in alerting delays to avoid false-positives. On the other hand, Robusta is event-driven and
    alerts based on discrete events. It notifies immediately without alerting delays and has rate-limiting features
    to avoid sending duplicate messages.

    When a Robusta playbook uses the ``on_prometheus_alert`` trigger, there is a delay on the Prometheus end before
    alerts ever reach Robusta. Once the alert reaches Robusta, the playbook executes immediately.

We can wait for the alert to fire or we can speed things up and simulate the alert, as if it fired immediately:

.. code-block:: bash

    Show alert simulation

Once the alert fires, a notification arrives in your configured sinks:

.. TODO example image

Enriching the Alert
------------------------------------

In the next tutorial, we enhance this Prometheus alert with Robusta. Keep reading to learn more:

* :ref:`Enrich Custom Prometheus Alerts`
