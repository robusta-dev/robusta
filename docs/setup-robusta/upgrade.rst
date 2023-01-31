Upgrade
#########

Most upgrades can be performed with two Helm commands. We call this a "Simple Upgrade".

Some upgrades require additional steps, as described in the "Manual Upgrade" section.

Simple Upgrade
^^^^^^^^^^^^^^^^^^^^^
To preserve your existing settings, you'll need the ``generated_values.yaml`` file that you
originally installed Robusta with.

.. admonition:: Where is my generated_values.yaml?

    If you have lost your ``generated_values.yaml`` file, you can extract it from any cluster with Robusta:

    .. code-block:: bash

         helm get values -o yaml robusta > generated_values.yaml

Once you've located your ``generated_values.yaml`` file, run the following:

.. code-block:: bash

    helm repo update
    helm upgrade robusta robusta/robusta --values=generated_values.yaml

.. admonition:: Can I run ``helm upgrade --reuse-values``?

    We recommend against it. `The --reuse-values flag doesn't respect certain Chart changes. <https://medium.com/@kcatstack/understand-helm-upgrade-flags-reset-values-reuse-values-6e58ac8f127e>`_

Verify that Robusta is running and there are no errors in the logs:

.. code-block:: bash

    robusta logs


Manual Upgrade
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some scenarios, manual actions are required in addition to running ``helm upgrade``.

Do I need to do a manual upgrade?
------------------------------------
You need a manual upgrade when **both** of the following are true:

* You're upgrading from a Robusta version lower than 0.9.1
* You are using Robusta's embedded Prometheus stack (``enablePrometheusStack: true``)

Why are manual upgrades necessary?
------------------------------------

Robusta uses kube-prometheus-stack, which creates custom resources known as `CRDs <https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/>`_.
With Helm v3, CRDs are not updated or removed by default and should be manually handled. Consult also the `Helm Documentation on CRDs <https://helm.sh/docs/chart_best_practices/custom_resource_definitions/>`_.

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

.. code-block:: bash

    helm repo update && helm upgrade robusta robusta/robusta -f ./generated_values.yaml

5. Verify that Robusta is running and there are no errors in the logs:

.. code-block:: bash

    robusta logs

Pre-release Upgrade
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes we release beta versions of Robusta. Normally, Helm ignores these versions and will only consider stable
versions when upgrading.

To upgrade to beta versions of Robusta, run ``helm upgrade`` with the ``--devel`` flag.
