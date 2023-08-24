Upgrade and Uninstall
######################

Most upgrades are just ``helm upgrades``, but some upgrades require manual steps.

What type of upgrade do I need?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You need a :ref:`Manual Upgrade` when both:

* Robusta's old version is lower than 0.10.17 (run ``helm list`` to check)
* The embedded Prometheus is enabled (``enablePrometheusStack: true``)

In all other cases, do a :ref:`Simple Upgrade`.

Simple Upgrade
^^^^^^^^^^^^^^^^^^^^^

Find the ``generated_values.yaml`` you installed Robusta with. You'll need this to preserve settings during the upgrade.

.. _where-is-generated-values:

.. details:: Where is my generated_values.yaml?

    If you lost your ``generated_values.yaml`` file, you can extract it from any cluster with Robusta:

    .. code-block:: bash

         helm get values -o yaml robusta > generated_values.yaml

Now do a helm upgrade, passing your existing settings:

.. include:: ./_helm_upgrade.rst

.. warning:: Do **not** run ``helm upgrade --reuse-values``

    `The --reuse-values flag doesn't respect all Chart changes. <https://medium.com/@kcatstack/understand-helm-upgrade-flags-reset-values-reuse-values-6e58ac8f127e>`_

Verify that Robusta is running and there are no errors in the logs:

.. code-block:: bash

    robusta logs


Manual Upgrade
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some upgrades require minor additional steps.

Why are manual upgrades necessary?
------------------------------------

Robusta bundles kube-prometheus-stack, which uses `CRDs <https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/>`_.
Helm can't update CRDs, so we update them ourselves. See the `Helm Documentation on CRDs <https://helm.sh/docs/chart_best_practices/custom_resource_definitions/>`_ for details.

Upgrading from older versions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Follow the steps below to fix any issues with old CRDs

1. The node-exporter daemonset and admission webhooks needs to be manually removed prior to upgrading:

.. code-block:: bash

    kubectl delete daemonset -l app=prometheus-node-exporter
    kubectl delete validatingwebhookconfigurations.admissionregistration.k8s.io -l app=kube-prometheus-stack-admission
    kubectl delete MutatingWebhookConfiguration -l app=kube-prometheus-stack-admission

2. Manually update the installed CRDs. For more info, refer to the `kube-prometheus-stack docs <https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack#uninstall-chart>`_.

.. warning:: If you have an existing Prometheus Operator installed independently of Robusta then be very careful! Upgrading CRDs will impact all Prometheus Operators in your cluster.

.. code-block:: bash

    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.66.0/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagerconfigs.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.66.0/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagers.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.66.0/example/prometheus-operator-crd/monitoring.coreos.com_podmonitors.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.66.0/example/prometheus-operator-crd/monitoring.coreos.com_probes.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.66.0/example/prometheus-operator-crd/monitoring.coreos.com_prometheuses.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.66.0/example/prometheus-operator-crd/monitoring.coreos.com_prometheusrules.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.66.0/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml
    kubectl replace -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.66.0/example/prometheus-operator-crd/monitoring.coreos.com_thanosrulers.yaml

3. Update Robusta with Helm. If you've lost ``generated_values.yaml``, you can :ref:`extract it from the cluster.<where-is-generated-values>`

.. include:: ./_helm_upgrade.rst

4. Verify that Robusta is running and there are no errors in the logs:

.. code-block:: bash

    robusta logs

Installing pre-releases
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install beta version of Robusta with ``helm upgrade --devel``.

Uninstall
^^^^^^^^^^

You can uninstall Robusta as follows:

.. code-block:: bash

    helm uninstall robusta
