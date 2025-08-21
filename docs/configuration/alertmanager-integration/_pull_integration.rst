Configure Metric Querying
====================================

To enable Robusta to pull metrics and create silences, you need to configure Prometheus and AlertManager URLs.

See :doc:`Prometheus and metrics configuration </configuration/metric-providers-in-cluster>` for detailed instructions.

.. note::

    Robusta will attempt to auto-detect Prometheus and AlertManager URLs in your cluster. Manual configuration is only needed if auto-detection fails.