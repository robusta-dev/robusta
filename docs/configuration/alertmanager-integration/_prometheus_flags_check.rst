Robusta utilizes the flags API to retrieve data from Prometheus-style metric stores. However, some platforms like Google Managed Prometheus, Azure Managed Prometheus etc, do not implement the flags API.

You can disable the Prometheus flags API check by setting the following option to false.

.. code-block:: yaml

    globalConfig:
      check_prometheus_flags: true/false