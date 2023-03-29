:hide-toc:

Multi-cluster
##############################

Have more than one Kubernetes cluster to monitor? Follow the instructions here.

Installing Robusta on multiple clusters
------------------------------------------

1. Install Robusta on the first cluster, as described in :ref:`Quick Install`.

2. Do a ``helm install`` on each additional cluster, **re-using** your existing ``generated_values.yaml``.

   .. code-block:: bash
      :name: cb-helm-install-only-robusta

       helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

.. warning::

      Do **not** run ``robusta gen-config`` separately for each cluster. That will give each cluster a unique ``generated_values.yaml`` which you don't want!

Frequently Asked Questions
----------------------------

Why not run ``robusta gen-config`` separately for each cluster?
*******************************************************

Each time you run ``robusta gen-config``, it creates a new account ID. The Robusta UI groups all your clusters by that ID.

If you run ``robusta gen-config`` once per cluster, you wont be able to view all your clusters together.

Where is my ``generated_values.yaml``?
*******************************************************

If you lost your ``generated_values.yaml`` file, you can extract it from any cluster running Robusta.

.. code-block:: bash

    helm get values -o yaml robusta | grep -v clusterName: | grep -v isSmallCluster: > generated_values.yaml

.. note::

      The above command strips the ``clusterName`` and ``isSmallCluster`` options so you don't copy them accidentally.
      These options should be determined on a cluster by cluster basis.
