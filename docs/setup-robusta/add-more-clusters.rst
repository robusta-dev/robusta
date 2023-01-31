:hide-toc:

Add more clusters
##############################

Install Robusta on your first cluster, following the :ref:`usual instructions <Quick Install>`.

For additional clusters, do **not** re-run ``robusta gen-config``.

Instead, re-use the ``generated_values.yaml`` file created for the first cluster, modifying only the ``clusterName``
setting each time.

.. code-block:: bash
   :name: cb-helm-install-only-robusta

    helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME> # --set isSmallCluster=true

Frequently Asked Questions
----------------------------

Why not run ``robusta gen-config`` for each cluster?
*******************************************************

Each time you run ``robusta gen-config``, it creates a new account ID.
This ID is used in the Robusta UI to group all your clusters into a single account.

If you run ``robusta gen-config`` once per cluster, your clusters will be in different accounts.

Where is ``generated_values.yaml``?
*******************************************************

If you have lost your ``generated_values.yaml`` file, you can extract it from any cluster running Robusta.

.. code-block:: bash

    helm get values -o yaml robusta | grep -v clusterName: | grep -v isSmallCluster: > generated_values.yaml

The above command strips the ``clusterName`` and ``isSmallCluster`` options to prevent you from accidentally copying
them to a new cluster. These options should be determined on a cluster by cluster basis.
