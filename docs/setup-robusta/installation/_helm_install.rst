Install with Helm
------------------------------

Copy the below commands, replacing the ``<YOUR_CLUSTER_NAME>`` placeholder.

On some clusters this can take a while, so don't panic if it appears stuck:

.. tab-set::

    .. tab-item:: Normal Clusters
        :name: install-standard

        .. code-block:: bash
            :name: cb-helm-install-only-robusta

            helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
            helm install robusta robusta/robusta -f ./generated_values.yaml \
                --set clusterName=<YOUR_CLUSTER_NAME>

    .. tab-item:: OpenShift
        :name: install-openshift

        Install as usual, :ref:`then grant relevant permissions<openshift-permissions>`.

        .. code-block:: bash
            :name: cb-helm-install-test-clusters

            helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
            helm install robusta robusta/robusta -f ./generated_values.yaml \
                --set clusterName=<YOUR_CLUSTER_NAME> \
                --set isSmallCluster=true


    .. tab-item:: GKE Autopilot
        :name: install-gke-autopilot

        Due to Autopilot restrictions, some components are disabled for Robusta's bundled Prometheus. Don't worry, everything will still work.

        .. code-block:: bash
            :name: cb-helm-install-gke-autopilot

            helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
            helm install robusta robusta/robusta -f ./generated_values.yaml \
                --set clusterName=<YOUR_CLUSTER_NAME> \
                --set kube-prometheus-stack.coreDns.enabled=false \
                --set kube-prometheus-stack.kubeControllerManager.enabled=false \
                --set kube-prometheus-stack.kubeDns.enabled=false \
                --set kube-prometheus-stack.kubeEtcd.enabled=false \
                --set kube-prometheus-stack.kubeProxy.enabled=false \
                --set kube-prometheus-stack.kubeScheduler.enabled=false \
                --set kube-prometheus-stack.nodeExporter.enabled=false \
                --set kube-prometheus-stack.prometheusOperator.kubeletService.enabled=false

    .. tab-item:: Kind/Colima
        :name: install-test-clusters

        Test clusters tend to have fewer resources. To lower Robusta's resource requests, set ``isSmallCluster=true``.

        .. code-block:: bash
            :name: cb-helm-install-test-clusters

            helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
            helm install robusta robusta/robusta -f ./generated_values.yaml \
                --set clusterName=<YOUR_CLUSTER_NAME> \
                --set isSmallCluster=true

Verifying Installation
------------------------------

Confirm that two Robusta pods are running with no errors in the logs:

.. code-block:: bash
    :name: cb-get-pods-robusta-logs

    kubectl get pods -A | grep robusta
    robusta logs