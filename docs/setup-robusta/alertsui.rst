Alerts UI
######################

With the Robusta Alerts UI, you can create and customize Prometheus Rules using templates, without needing to know PromQL.

.. image:: /images/robusta-ui-alerts-ui.gif

This guide covers how it works, and also the steps involved to use this feature:

* Enable the Alerts UI on the Robusta UI.
* Disable default Prometheus alerts installed by Kube Prometheus Stack.


How it works
--------------------

Activating this feature automatically generates a predefined collection of PrometheusRule custom resources.

These alerts are seamlessly synchronized from the Robusta platform to any cluster that has this functionality activated, by created PrometheusCRD files in the cluster.

You can to enable, disable, or adjust these alerts through the user interface.

The alerts originate from the Kube Prometheus Stack, with plans to add additional alerts in the future.

Activate Alerts Interface
--------------------------
To see alerts and customize them, you must first activate alert rules in the Robusta UI.

1. Go to `platform.robusta.dev <https://platform.robusta.dev/>`_ -> Alerting -> Alerts
2. Click the "Enable Alert Rules" button.

.. image:: /images/click-enable-alert-rules.png



Disable Default Prometheus Alert Rules
********************************************

Since Robusta creates new PrometheusRule custom resources, you must disable the default Kube Prometheus Stack alerts to avoid duplication of alerts.

Choose the appropriate instructions below, based on whether you use the Prometheus bundled with Robusta or your own Prometheus.

.. tab-set::

.. tab-set::
   .. tab-item:: Robusta’s Prometheus

      To start syncing alerts to your cluster and to avoid duplication, add the following snippet to Robusta’s Helm values file named ``generated_values.yaml``:

      .. code-block:: yaml

        enabledManagedConfiguration: true # Enable managed alerts (See 1.)
        kube-prometheus-stack: # those rules are now managed by Robusta
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

      Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

   .. tab-item:: External Prometheus

      First, ensure you have the Prometheus operator installed by running the following command:

      .. code-block:: bash

         kubectl get crd | grep prometheus

      If you're using kube-prometheus-stack and its default alerts, add the following to its configuration to avoid duplication:

      .. code-block:: yaml

        defaultRules: # those rules are now managed by Robusta
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

      Adjust your Prometheus configuration so it will pick up Robusta's PrometheusRule files:

      .. code-block:: yaml

        prometheus:
            ruleNamespaceSelector: {}
            ruleSelector: {}
            ruleSelectorNilUsesHelmValues: false

      Note: These changes allow Prometheus to collect rules from all namespaces and ignore label filters, ensuring it will pick Robusta's PrometheusRule files.

      Finally, to start syncing alerts to your cluster, add the following snippet to Robusta’s Helm values file named ``generated_values.yaml``:

      .. code-block:: yaml

        enabledManagedConfiguration: true # Enable managed alerts

      Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.


Disabling the Feature
---------------------------------

If you choose to stop using the Robusta Alerts UI, you can do so at any time and go back to using built in Kube Prometheus Stack alerts. To do this, remove the config added in the previous step from your ``generated_values.yaml`` and do a :ref:`Helm Upgrade <Simple Upgrade>`.

Robusta stores its managed rules in PrometheusRules custom resources that start with ``robusta-prometheus.rules--``. If left in the cluster, you might have double alerts.

Modify and run the following command for all the Robusta rule custom resources present in your cluster.

.. code-block:: bash

    kubectl delete prometheusrules.monitoring.coreos.com robusta-prometheus.rules--Value -n NameSpace
