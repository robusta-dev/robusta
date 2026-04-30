:hide-toc:

Multi-cluster
##############################

This guide is for environments with more than one Kubernetes cluster.

It's important to add all clusters to the same Robusta account.

Installing Robusta on multiple clusters
------------------------------------------

1. Install Robusta on the first cluster, as described in :ref:`install`.

2. Do a ``helm install`` on each additional cluster, **re-using** your existing ``generated_values.yaml``.

   .. code-block:: bash
      :name: cb-helm-install-only-robusta

       helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

.. warning::

      Set a unique ``clusterName`` on each cluster (via ``--set clusterName=<YOUR_CLUSTER_NAME>``). The rest of ``generated_values.yaml`` stays the same across all clusters — that's how the Robusta UI groups them under the same account.

Frequently Asked Questions
----------------------------

Where is my ``generated_values.yaml``?
*******************************************************

If you lost your ``generated_values.yaml`` file, you can extract it from any cluster running Robusta.

.. code-block:: bash

    helm get values -o yaml robusta | grep -v clusterName: | grep -v isSmallCluster: > generated_values.yaml

.. note::

      The above command strips the ``clusterName`` and ``isSmallCluster`` options so you don't copy them accidentally.
      These options should be determined on a cluster by cluster basis.
