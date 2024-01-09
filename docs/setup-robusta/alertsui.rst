Alerts UI
######################

With the Robusta Alerts UI, you can create and customize Prometheus Rules using templates, without needing to know PromQL.

.. image:: /images/robusta-ui-alerts-ui.gif

This guide covers enabling managed alerts with the Robusta UI. This involves two steps:

* Enable the Alert UI on the Robusta UI.
* Disable default Prometheus alerts installed by Kube Prometheus Stack.

.. note::

    To use the Alerts UI, you must use Robusta's :ref:`Embedded Prometheus Stack`.

Activate Alerts Interface
--------------------------

To see alerts and customize them, you must first activate alert rules in the Robusta UI.

1. Go to `platform.robusta.dev <https://platform.robusta.dev/>`_ -> Alerting -> Alerts
2. Click the "Enable Alert Rules" button.

.. image:: /images/click-enable-alert-rules.png



Disable Default Alert Rules
********************************************

To avoid duplication of alerts, you must disable the default Kube Prometheus Stack alerts. Add the following config to your ``generated_values.yaml``.

.. code-block:: yaml

    enabledManagedConfiguration: true # (1)
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

.. code-annotations::
    1. Creates Robusta managed alerts in your cluster.

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.


Disabling the Feature
---------------------------------

If you choose to stop using the Robusta alerts UI, you can do so at any time and go back to using built in Kube Prometheus Stack alerts. To do this, remove the config added in the previous step from your ``generated_values.yaml`` and do a :ref:`Helm Upgrade <Simple Upgrade>`.

Robusta stores its managed rules in PrometheusRules custom resources that start with ``robusta-prometheus.rules--``. If left in the cluster, you might have double alerts.

Modify and run the following command for all the Robusta rule custom resources present in your cluster.

.. code-block:: bash

    kubectl delete prometheusrules.monitoring.coreos.com robusta-prometheus.rules--Value -n NameSpace
