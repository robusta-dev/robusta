Supported Clusters
################################

We support all Kubernetes distributions other than Minikube.

Distribution-specific instructions are below.


.. _openshift-permissions:

OpenShift
========================================

OpenShift is supported. Robusta needs to be granted permissions to run:

.. code-block:: bash
   :name: cb-oc-adm-policy-add

    oc adm policy add-scc-to-user anyuid -z robusta-forwarder-service-account
    oc adm policy add-scc-to-user anyuid -z robusta-runner-service-account

The above permissions are very loose. More restrictive policies can be applied too.

Minikube
==========
We don't recommend installing Robusta on Minikube, due to a Minikube bug. For more details, refer to `this GitHub issue <https://github.com/kubernetes/minikube/issues/14806>`_.

We recommend testing with KIND instead.

Other Kubernetes Providers
================================

.. TODO add details here about silencing for specific providers

We have also tested Robusta on:

* EKS
* GKE
* AKS
* Civo Cloud
* Digital Ocean
* KIND
* RKE
