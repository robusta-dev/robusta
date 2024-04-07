Supported Clusters
################################

Robusta supports all Kubernetes distributions other than Minikube, including:

* EKS
* GKE
* AKS
* Civo Cloud
* Digital Ocean
* KIND
* RKE
* :ref:`Openshift <Openshift>`

Minikube
==========
We don't recommend installing Robusta on Minikube, due to a Minikube bug. For more details, refer to `this GitHub issue <https://github.com/kubernetes/minikube/issues/14806>`_.

Instead, we recommend testing Robusta with KIND.


.. TODO add details here about silencing for specific providers
