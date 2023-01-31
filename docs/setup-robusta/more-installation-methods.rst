Other installation notes
################################

This page documents:

* Environments that Robusta supports
* Non-default installation options you can choose.

Supported Kubernetes Clusters
========================================
We support all Kubernetes distributions, with the following caveats:

* OpenShift is supported but requires :ref:`one extra step when installing <Installing on OpenShift>`.
* Minikube is not supported. We recommend using KIND for test clusters.

Companies are known to be using Robusta on: EKS, GKE, AKS, OpenShift, RKE, Civo, Digital Ocean, and KIND.

Using Robusta on a cloud not listed above? `Tell us <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=other.md&title=>`_ and we'll update the list.

Installing without the Robusta CLI
========================================

Using the cli is totally optional. If you prefer, you can skip the CLI and fetch the default **Helm values** from the helm chart:

.. code-block:: bash
    :name: cb-helm-repo-add-show-values

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
    helm show values robusta/robusta


Most values are documented in the :ref:`Configuration Guide`

Do not use ``helm/robusta/values.yaml`` in the GitHub repo. It has some empty placeholders which are replaced during
our release process.

Installing in a different namespace
========================================


Create a namespace ``robusta`` and install robusta in the new namespace using:

.. code-block:: bash
    :name: cb-helm-install-robusta-custom

    helm install robusta robusta/robusta -f ./generated_values.yaml -n robusta --create-namespace

Verify that Robusta installed two deployments in the ``robusta`` namespace:

.. code-block:: bash
   :name: cb-get-pods-robusta-logs-custom

    kubectl get pods -n robusta

.. warning::

    If you change Robusta's namespace, make sure to add the ``--namespace`` flag to future ``robusta`` cli commands.

Installing on OpenShift
========================================

When installing Robusta on OpenShift, you will need to run an additional command:

.. code-block:: bash
   :name: cb-oc-adm-policy-add

    oc adm policy add-scc-to-user anyuid -z robusta-runner-service-account

This command grants Robusta slightly higher permissions than it actually needs. Please feel free to open a PR suggesting something more minimal.
