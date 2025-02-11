Robusta
====

Fetches alerts metadata and change history

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
    holmes:

        toolsets:
            robusta:
                enabled: true


.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - fetch_finding_by_id
     - Fetches a robusta finding. Findings are events, like a Prometheus alert or a deployment update
