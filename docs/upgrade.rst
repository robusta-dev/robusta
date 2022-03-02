Upgrade Guide
##################

Robusta is installed with Helm, so Robusta upgrades are just Helm upgrades.

.. warning:: Upgrading an existing Release with bundled Prometheus Stack might require manual actions. :ref:`Read here <Upgrading with bundled Prometheus Stack>`

Helm Upgrade
------------------------------

This will upgrade Robusta while preserving any custom settings:

.. code-block:: bash

    helm repo update
    helm upgrade robusta robusta/robusta --values=values.yaml

We recommend running the above command exactly as written.

.. admonition:: Where is my values.yaml?

    If you have lost your ``values.yaml`` file, you can extract it from the cluster:

    .. code-block:: bash

         helm get values robusta

Notes
^^^^^^^^^^^^^^^^^^^^^^^^
1. We do **not** recommend running ``helm upgrade --reuse-values`` `as it doesn't update default values changed in the chart.
<https://medium.com/@kcatstack/understand-helm-upgrade-flags-reset-values-reuse-values-6e58ac8f127e>`_

2. To install a Robusta pre-release, run ``helm upgrade`` with the ``--devel`` flag.

Upgrading with bundled Prometheus Stack
----------------------------------------

If you didn't install Robusta's bundled Prometheus Stack then you can :ref:`Upgrade at ease <Helm Upgrade>`, Otherwise, keep reading.

1. Why do I need to manually upgrade?

Robusta uses kube-prometheus-stack, which creates custom resources also known as `CRDs <https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/>`_ on installation.     
With Helm v3, CRDs are not updated or removed by default and should be manually handled. Consult also the `Helm Documentation on CRDs <https://helm.sh/docs/chart_best_practices/custom_resource_definitions/>`_. 

From 0.8.x to >= 0.9.x 
^^^^^^^^^^^^^^^^^^^^^^^^

1. Check robusta version, look under Robusta:

.. code-block:: bash

    helm list

2. Due to the upgrade of the dependency, kube-state-metrics chart, removal of its deployment/stateful needs to be done manually prior to upgrading:

.. code-block:: bash

    kubectl delete deployment robusta-kube-state-metrics robusta-kube-prometheus-st-operator  --cascade=orphan

3. Manually update the installed CRDs (`for more info read here <https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack#uninstall-chart>`_):

.. warning:: If you have an existing Prometheus Operator installed independently of Robusta then be very careful! Upgrading CRDs will impact all Prometheus Operators in your cluster.

.. code-block:: bash

    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.54.0/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagerconfigs.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.54.0/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagers.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.54.0/example/prometheus-operator-crd/monitoring.coreos.com_podmonitors.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.54.0/example/prometheus-operator-crd/monitoring.coreos.com_probes.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.54.0/example/prometheus-operator-crd/monitoring.coreos.com_prometheuses.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.54.0/example/prometheus-operator-crd/monitoring.coreos.com_prometheusrules.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.54.0/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.54.0/example/prometheus-operator-crd/monitoring.coreos.com_thanosrulers.yaml

4. Update helm chart and upgrade Robusta:

.. code-block:: bash

    helm repo update && helm upgrade robusta robusta/robusta -f ./generated_values.yaml