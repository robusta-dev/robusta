Supported Clusters
################################

We support all Kubernetes distributions other than Minikube.

Distribution-specific instructions are below.

OpenShift
========================================

OpenShift is supported. Install as usual. Then grant Robusta permissions:

.. code-block:: bash
   :name: cb-oc-adm-policy-add

    oc adm policy add-scc-to-user anyuid -z robusta-forwarder-service-account
    oc adm policy add-scc-to-user anyuid -z robusta-runner-service-account

Minikube
==========
Minikube is not supported. We recommend testing with KIND instead.

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
