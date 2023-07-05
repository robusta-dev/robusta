Configuring a Pull Integration
====================================

.. For certain features, Robusta needs to reach out to Prometheus and pull in extra information. This must
.. be configured **in addition** to updating AlertManager's configuration.

.. That said, most users won't need to set this up.Robusta can usually figure out where Prometheus and
.. other services are located. If the auto-discovery isn't working, you'll configure it manually.

Add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

    globalConfig: # this line should already exist
        # add the lines below
        alertmanager_url: "http://ALERT_MANAGER_SERVICE_NAME.NAMESPACE.svc.cluster.local:9093" # (1)
        grafana_url: ""
        prometheus_url: "http://PROMETHEUS_SERVICE_NAME.NAMESPACE.svc.cluster.local:9090" # (2)
        # Additional query string parameters to be appended to the Prometheus connection URL (optional)
        prometheus_url_query_string: "demo-query=example-data&another-query=value"
.. code-annotations::
    1. Example: http://alertmanager-Helm_release_name-kube-prometheus-alertmanager.default.svc.cluster.local:9093.
    2. Example: http://Helm_Release_Name-kube-prometheus-prometheus.default.svc.cluster.local:9090
