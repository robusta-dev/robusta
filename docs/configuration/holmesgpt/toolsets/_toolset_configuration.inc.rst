

Update your Helm values (generated_values.yaml) with the above configuration and run a Helm upgrade:

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>
