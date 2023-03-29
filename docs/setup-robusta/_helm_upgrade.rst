.. code-block:: bash

    helm repo update
    helm upgrade robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>
