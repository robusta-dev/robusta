Upgrade
#########

Most upgrades are just ``helm upgrades``, but some upgrades require manual steps.

What type of upgrade do I need?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You need a :ref:`Manual Upgrade` when **both** of the following are true:

* You're upgrading from a Robusta version lower than 0.9.1
* You're using Robusta's embedded Prometheus stack (``enablePrometheusStack: true``)

In all other cases, do a :ref:`Simple Upgrade`.

Simple Upgrade
^^^^^^^^^^^^^^^^^^^^^
First, find the ``generated_values.yaml`` you installed Robusta with. You'll need this to preserve your settings during the upgrade.

.. admonition:: Where is my generated_values.yaml?

    If you lost your ``generated_values.yaml`` file, you can extract it from any cluster with Robusta:

    .. code-block:: bash

         helm get values -o yaml robusta > generated_values.yaml

Now do a helm upgrade, passing your existing settings:

.. include:: ./_helm_upgrade.rst

.. admonition:: Can I run ``helm upgrade --reuse-values``?

    No. `The --reuse-values flag doesn't respect all Chart changes. <https://medium.com/@kcatstack/understand-helm-upgrade-flags-reset-values-reuse-values-6e58ac8f127e>`_

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

Upgrading from versions lower than 0.9.1
------------------------------------------

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

4. Update helm chart and upgrade Robusta (:ref:`where is my generated_values.yaml <Where is my generated_values.yaml?>`):

.. include:: ./_helm_upgrade.rst

5. Verify that Robusta is running and there are no errors in the logs:

.. code-block:: bash

    robusta logs

Installing pre-releases
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install a beta version of Robusta, run ``helm upgrade --devel``.