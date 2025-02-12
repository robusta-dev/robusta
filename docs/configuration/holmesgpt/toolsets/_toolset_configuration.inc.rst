

.. details:: Enable this integration

    To enable this integration, copy the above example into your Helm values for Robusta (``generated_values.yaml``).

    After making changes, apply them using Helm:

    .. code-block:: bash

        helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>
