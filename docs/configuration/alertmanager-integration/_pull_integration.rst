Configuring a Pull Integration
====================================

.. For certain features, Robusta needs to reach out to Prometheus and pull in extra information. This must
.. be configured **in addition** to updating AlertManager's configuration.

.. That said, most users won't need to set this up.Robusta can usually figure out where Prometheus and
.. other services are located. If the auto-discovery isn't working, you'll configure it manually. 

Add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

    # this line should already exist
    globalConfig:
        # add the lines below
        alertmanager_url: ""
        grafana_url: ""
        prometheus_url: "http://PROMETHEUS_SERVICE_NAME.monitoring.svc.cluster.local:9090"
