Upgrade and Uninstall
######################

Robusta is installed with Helm, so Robusta upgrades are just Helm upgrades. Uninstalls are just Helm uninstalls.

.. warning:: Upgrading an existing release with bundled Prometheus Stack might require manual actions. :ref:`Read here <Upgrading with bundled Prometheus Stack>`

Helm Upgrade
------------------------------

This will upgrade Robusta while preserving any custom settings:

.. code-block:: bash

    helm repo update
    helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

We recommend running the above command by changing nothing more than the "clusterName".

.. _values-file:

.. admonition:: Where is my generated_values.yaml?

    If you have lost your ``generated_values.yaml`` file, you can extract it from the cluster:

    .. code-block:: bash

         helm get values -o yaml robusta > generated_values.yaml


Verify that Robusta is running and there are no errors in the logs:

.. code-block:: bash

    robusta logs

Notes
^^^^^^^^^^^^^^^^^^^^^^^^
1. We do **not** recommend running ``helm upgrade --reuse-values`` `as it doesn't update default values changed in the chart.
<https://medium.com/@kcatstack/understand-helm-upgrade-flags-reset-values-reuse-values-6e58ac8f127e>`_

2. To install a Robusta pre-release, run ``helm upgrade`` with the ``--devel`` flag.

Upgrading with bundled Prometheus Stack
----------------------------------------

If you didn't install Robusta's bundled Prometheus Stack then you can :ref:`upgrade at ease <Helm Upgrade>`. Otherwise, keep reading.

Why do I need to manually upgrade?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta uses kube-prometheus-stack, which creates custom resources also known as `CRDs <https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/>`_ on installation.
With Helm v3, CRDs are not updated or removed by default and should be manually handled. Consult also the `Helm Documentation on CRDs <https://helm.sh/docs/chart_best_practices/custom_resource_definitions/>`_.

From versions lower than 0.10.8 to latest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Determine Robusta's version by running the following:

.. code-block:: bash

    helm list

2. The node-exporter daemonset and admission webhooks needs to be manually removed prior to upgrading:

.. code-block:: bash

    kubectl delete daemonset -l app=prometheus-node-exporter
    kubectl delete validatingwebhookconfigurations.admissionregistration.k8s.io -l app=kube-prometheus-stack-admission
    kubectl delete MutatingWebhookConfiguration -l app=kube-prometheus-stack-admission

3. Manually update the installed CRDs (`for more info read here <https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack#uninstall-chart>`_):

.. warning:: If you have an existing Prometheus Operator installed independently of Robusta then be very careful! Upgrading CRDs will impact all Prometheus Operators in your cluster.

.. code-block:: bash

    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.61.1/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagerconfigs.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.61.1/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagers.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.61.1/example/prometheus-operator-crd/monitoring.coreos.com_podmonitors.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.61.1/example/prometheus-operator-crd/monitoring.coreos.com_probes.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.61.1/example/prometheus-operator-crd/monitoring.coreos.com_prometheuses.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.61.1/example/prometheus-operator-crd/monitoring.coreos.com_prometheusrules.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.61.1/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.61.1/example/prometheus-operator-crd/monitoring.coreos.com_thanosrulers.yaml

4. Update helm chart and upgrade Robusta (:ref:`where is my generated_values.yaml <values-file>`):

.. code-block:: bash

    helm repo update && helm upgrade robusta robusta/robusta -f ./generated_values.yaml

5. Verify that Robusta is running and there are no errors in the logs:

.. code-block:: bash

    robusta logs


Helm Uninstall
------------------------------

This will uninstall Robusta:

.. code-block:: bash

    helm uninstall robusta
