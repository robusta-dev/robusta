Monitoring Large Clusters
=========================

Memory Allocation on Big Clusters
----------------------------------

On bigger clusters, increase Robusta's memory ``requests`` and ``limits``.

Add this to Robusta's Helm values:

.. code-block:: yaml

    runner:
      resources:
        requests:
          memory: 2048Mi
        limits:
          memory: 2048Mi
