Upgrade Guide
##################

Robusta is installed with Helm, so Robusta upgrades are just Helm upgrades.

.. warning:: Upgrading an existing Release to a new major version might require manual actions. :ref:`read here <Upgrading to a new major version>`

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

Upgrading to a new major version
------------------------------

If you didnt install Robusta's bundled Prometheus Stack then you can :ref:`Upgrade at ease <Helm Upgrade>`, Otherwise, keep reading.

1. Why do i need to manually upgrade?

Robusta uses Prometheus Stack as a dependency, Prometheus creates Custom resources also known as `CRDs <https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/>`_ on installation.     
With Helm v3, CRDs are not updated or removed by default and should be manually handled. Consult also the `Helm Documentation on CRDs <https://helm.sh/docs/chart_best_practices/custom_resource_definitions/>`_. 

From 0.8.x to >= 0.9.x 
^^^^^^^^^^^^^^^^^^^^^^^^

1. Check robusta version:

.. code-block:: bash

    robusta version

2. We suggest removing and installing for the smoothest experience, start by uninstalling Robusta:

.. code-block:: bash

    helm uninstall robusta

3. Manually remove the instlled CRDs (`for more info read here <https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack#uninstall-chart>`_):

.. code-block:: bash

    kubectl delete crd alertmanagerconfigs.monitoring.coreos.com
    kubectl delete crd alertmanagers.monitoring.coreos.com
    kubectl delete crd podmonitors.monitoring.coreos.com
    kubectl delete crd probes.monitoring.coreos.com
    kubectl delete crd prometheuses.monitoring.coreos.com
    kubectl delete crd prometheusrules.monitoring.coreos.com
    kubectl delete crd servicemonitors.monitoring.coreos.com
    kubectl delete crd thanosrulers.monitoring.coreos.com

4. Update helm chart and install Robusta:

.. code-block:: bash

    helm repo update && helm install robusta robusta/robusta -f ./generated_values.yaml