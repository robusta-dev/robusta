Helm
====

Read access to cluster's Helm charts and releases

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
    holmes:

        toolsets:
            helm/core:
                enabled: true


.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - helm_list
     - Use to get all the current helm releases
   * - helm_values
     - Use to gather Helm values or any released helm chart
   * - helm_status
     - Check the status of a Helm release
   * - helm_history
     - Get the revision history of a Helm release
   * - helm_manifest
     - Fetch the generated Kubernetes manifest for a Helm release
   * - helm_hooks
     - Get the hooks for a Helm release
   * - helm_chart
     - Get the hooks for a Helm release
   * - helm_notes
     - Show the notes provided by the Helm chart
