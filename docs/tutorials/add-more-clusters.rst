Add more clusters
=================

Install the Robusta helm chart on each cluster. You should use the same ``generated_values.yaml``, changing the **clusterName** option for each cluster.

.. admonition:: Common mistake
    :class: warning

    
    Don't run ``robusta gen-config`` multiple times, or each cluster will have a seperate account.

.. code-block:: bash
   :name: cb-helm-install-only-robusta

    helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME> # --set isSmallCluster=true

Where is my generated_values.yaml?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have lost your ``generated_values.yaml`` file, you can extract it from any cluster running Robusta.

.. code-block:: bash

    helm get values -o yaml robusta | grep -v clusterName: | grep -v isSmallCluster: > generated_values.yaml

The above command removes ``clusterName`` and ``isSmallCluster`` so that you dont accidentaly reuse values from a different cluster. Make sure to remove them before installing on the new cluster.



