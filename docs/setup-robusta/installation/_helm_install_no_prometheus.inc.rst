.. updated to .inc.rst because of "WARNING: duplicate label"

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
            helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

    .. tab-item:: EKS
        :name: install-eks

        To use all Robusta features, ensure storage is enabled on your cluster. If necessary, refer to the EKS documentation and install the `EBS CSI add-on <https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html#adding-ebs-csi-eks-add-on>`_

        .. details:: How do I know if my cluster has storage enabled?

            Try installing Robusta. If storage is not configured, you'll receive an error:

            .. code-block::

                PreBind plugin "VolumeBinding": binding volumes: timed out waiting for the condition

            Running ``kubectl get pvc -A`` will also show PersistentVolumeClaims in ``Pending`` state.

            In this case, follow the instructions above and enable storage for your cluster.

        .. code-block:: bash
            :name: cb-helm-install-eks

            helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
            helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

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

    .. tab-item:: OpenShift
        :name: install-openshift

        First :ref:`modify the Helm values to enable OpenShift support<openshift-permissions>`.

        Then install Robusta as usual with Helm:
        
        .. code-block:: bash
            :name: cb-helm-install-openshift

            helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
            helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

    .. tab-item:: Local/Test Cluster
        :name: install-test-clusters

        Test clusters tend to have fewer resources. To lower Robusta's resource requests, set ``isSmallCluster=true``.

        .. code-block:: bash
            :name: cb-helm-install-test-clusters

            helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
            helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME> --set isSmallCluster=true --set holmes.resources.requests.memory=512Mi
            
Verifying Installation
------------------------------

Confirm that Robusta pods are running with no errors in the logs:

.. code-block:: bash
    :name: cb-get-pods-robusta-logs

    kubectl get pods -A | grep robusta
    robusta logs
