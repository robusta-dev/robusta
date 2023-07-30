Supported Clusters
################################

We support all Kubernetes distributions other than Minikube.

Distribution-specific instructions are below.


.. _openshift-permissions:

OpenShift
========================================

OpenShift is supported via the Helm chart. 

.. warning::

      Do **not** install Robusta in the ``default`` OpenShift project.

Update the ``generated_values.yaml`` file to enable OpenShift support:

.. code-block:: yaml

    openshift:
      enabled: true
      createScc: true
    

For users that do not have access to create their own SCCs in the cluster, see the
`openshift-scc-baseline.yaml <../../helm/robusta/templates/openshift-scc-baseline.yaml>`_ file for the baseline SCC for the product. This SCC can be
created in advance by administrators and referenced using the following set of values:

.. code-block:: yaml

    openshift:
      enabled: true
      sccName: my-admins-scc

A test installation in OpenShift can use the existing SCC ``anyuid``.

OpenShift Prometheus Stack
--------------------------

OpenShift comes with an existing Prometheus installation. In order to point
to the preconfigued stack, update the ``globalConfig`` in the Helm values with
the following:

.. code-block:: yaml

    globalConfig:
      prometheus_url: http://prometheus-operated.openshift-monitoring.svc.cluster.local:9090

Robusta Advanced Debug Features
--------------------------------

In order to support the ``python_debugger``, ``java_debugger`` and ``node_disk_analyzer``
playbooks, permission to run a far more privileged container needs to be granted to
the ``runner`` service account. This container has ``SYS_ADMIN`` capabilities and must
run as root on the node.

To support these features in a production environment, you may want to only temporarily
enable this permission so that a normal request cannot bypass the the less permissive SCC found
in the baseline. To enable these privileged operations in your OpenShift environment,
update the ``generated_values.yaml`` as follows:

.. code-block:: yaml

    openshift:
      enabled: true
      createScc: true
      createPrivilegedScc: true

You may also reference an existing SCC using the ``openshift.privilegedSccName`` value.
In test environments, you can reference the ``privileged`` SCC to enable these features in your
installation.

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
