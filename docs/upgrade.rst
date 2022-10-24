Upgrade and Uninstall
######################

Robusta is :ref:`installed with Helm <Install with Helm>`, so Robusta upgrades are just Helm upgrades. Uninstalls are just Helm uninstalls.

Upgrading Robusta
^^^^^^^^^^^^^^^^^^^^^
To preserve your existing settings, you'll need the ``generated_values.yaml`` file that you
originally installed Robusta with.

.. admonition:: Where is my generated_values.yaml?

    If you have lost your ``generated_values.yaml`` file, you can extract it from any cluster Robusta is installed on:

    .. code-block:: bash

         helm get values -o yaml robusta > generated_values.yaml

Once you've located your ``generated_values.yaml`` file, run the following command:

.. code-block:: bash

    helm repo update
    helm upgrade robusta robusta/robusta --values=generated_values.yaml

We recommend running the above command exactly as written and **not** running ``helm upgrade --reuse-values`` `as it doesn't respect changes to default values. <https://medium.com/@kcatstack/understand-helm-upgrade-flags-reset-values-reuse-values-6e58ac8f127e>`_

.. warning:: Some upgrades require extra steps. If your ``generated_values.yaml`` contains the setting ``enablePrometheusStack: true`` then :ref:`read here <Upgrading with bundled Prometheus Stack>`


Verify that Robusta is running and there are no errors in the logs:

.. code-block:: bash

    robusta logs


2. To install a Robusta pre-release, run ``helm upgrade`` with the ``--devel`` flag.

Manual Upgrade Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some scenarios, manual actions are required in addition to running ``helm upgrade``.

If you're upgrading from a Robusta version lower than 0.9.1 **and** you're using the setting ``enablePrometheusStack`` than this applies to you. Otherwise, just upgrade as described above.

Why do I need to manually upgrade?
------------------------------------

Robusta uses kube-prometheus-stack, which creates custom resources known as `CRDs <https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/>`_.
With Helm v3, CRDs are not updated or removed by default and should be manually handled. Consult also the `Helm Documentation on CRDs <https://helm.sh/docs/chart_best_practices/custom_resource_definitions/>`_.

Upgrading from versions lower than 0.9.1
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Determine Robusta's version by running the following:

.. code-block:: bash

    helm list

2. The kube-state-metrics chart needs to be manually removed prior to upgrading:

.. code-block:: bash

    kubectl delete deployment robusta-kube-state-metrics robusta-kube-prometheus-st-operator  --cascade=orphan

3. Manually update the installed CRDs (`for more info read here <https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack#uninstall-chart>`_):

.. warning:: If you have an existing Prometheus Operator installed independently of Robusta then be very careful! Upgrading CRDs will impact all Prometheus Operators in your cluster.

.. code-block:: bash

    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.55.0/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagerconfigs.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.55.0/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagers.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.55.0/example/prometheus-operator-crd/monitoring.coreos.com_podmonitors.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.55.0/example/prometheus-operator-crd/monitoring.coreos.com_probes.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.55.0/example/prometheus-operator-crd/monitoring.coreos.com_prometheuses.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.55.0/example/prometheus-operator-crd/monitoring.coreos.com_prometheusrules.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.55.0/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.55.0/example/prometheus-operator-crd/monitoring.coreos.com_thanosrulers.yaml

4. Update helm chart and upgrade Robusta (:ref:`where is my generated_values.yaml <values-file>`):

.. code-block:: bash

    helm repo update && helm upgrade robusta robusta/robusta -f ./generated_values.yaml

5. Verify that Robusta is running and there are no errors in the logs:

.. code-block:: bash

    robusta logs


Uninstall
--------------

This will uninstall Robusta:

.. code-block:: bash

    helm uninstall robusta
