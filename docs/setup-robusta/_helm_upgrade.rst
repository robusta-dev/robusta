.. code-block:: bash

    helm repo update
    helm upgrade robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

Or using the OCI registry:

.. code-block:: bash

    helm upgrade robusta oci://ghcr.io/robusta-dev/charts/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>
