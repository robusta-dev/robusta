Alerts UI
######################

With Robusta Alerts UI, you can create and customize Prometheus Rules using templates, without needing to know PromQL.

.. image:: /images/managed-alerts-ui.png



This guide covers enabling managed alerts with Robusta UI. This involves two steps: One to enable the Alert Rules on the UI and another to disable default Prometheus alerts installed by Kube Prometheus Stack.

.. note::

    Alerts UI works only with Prometheus installed by Robusta. :ref:`Embedded Prometheus Stack`

Enable Alerts UI
--------------------

To start seeing all the alerts and customize them, we first need to enable Alert Rules in the Robusta UI.

1. Go to `platform.robusta.dev <https://platform.robusta.dev/>`_ -> Alerting -> Alerts
2. Click "Enable Alert Rules"

.. image:: /images/click-enable-alert-rules.png



Enable Robusta Managed Alerts
********************************************

Next we need to disable default Prometheus alerts from Kube Prometheus Stack and enable Robusta managed alerts. Add the following config to your ``generated_values.yaml``.

.. code-block:: yaml

    enabledManagedConfiguration: true
    kube-prometheus-stack:
    defaultRules:
        rules:
        alertmanager: false
        etcd: false
        configReloaders: false
        general: false
        kubeApiserverSlos: false
        kubeControllerManager: false
        kubeProxy: false
        kubernetesApps: false
        kubernetesResources: false
        kubernetesStorage: false
        kubernetesSystem: false
        kubeSchedulerAlerting: false
        kubeStateMetrics: false
        network: false
        nodeExporterAlerting: false
        prometheus: false
        prometheusOperator: false

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.


Disable Robusta Managed Alerts
---------------------------------

To go back to Kube Prometheus Satck built in alerts, remove the config added in the previous step from your ``generated_values.yaml``. Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Cleanup
*******************

Robusta stores its managed rules in PrometheusRules CR's that start with ``robusta-prometheus.rules--``. If left in the cluster, you might have double alerts.

Modify and run the following command for all the Robusta rule CR's present in your cluster.

.. code-block:: bash

    kubectl delete prometheusrules.monitoring.coreos.com robusta-prometheus.rules--Value -n NameSpace
