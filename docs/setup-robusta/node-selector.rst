Deploying to Specific Nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can run Robusta on specific nodes in your cluster. For example, on a hybrid Windows and Linux cluster, you'll want
to ensure Robusta runs on Linux nodes.

You can configure this using either ``nodeSelectors``, ``affinities`` or ``taints`` and ``tolerations``

Running Robusta on Linux Nodes
-------------------------------------

Add the following to your Helm values:

.. code-block:: yaml

    runner:
      nodeSelector:
        kubernetes.io/os: linux

    kubewatch:
      nodeSelector:
        kubernetes.io/os: linux

    # if using Robusta's embedded kube-prometheus-stack, you can configure the Prometheus Operator's components to run on a specific node too
    kube-prometheus-stack:
      alertmanager:
        alertmanagerSpec:
          nodeSelector: kubernetes.io/os: linux
      prometheus:
        prometheusSpec:
          nodeSelector: kubernetes.io/os: linux
      prometheusOperator:
        nodeSelector: kubernetes.io/os: linux
        admissionWebhooks:
          deployment:
            nodeSelector: kubernetes.io/os: linux
          patch:
            nodeSelector: kubernetes.io/os: linux
      kube-state-metrics:
        nodeSelector: kubernetes.io/os: linux
      grafana:
        nodeSelector: kubernetes.io/os: linux
      thanosRuler:
        thanosRulerSpec:
          nodeSelector: kubernetes.io/os: linux

Alternatively, you can configure this with nodeAffinities:

.. code-block:: yaml

    runner:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/os
                operator: In
                values:
                - linux

    kubewatch:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/os
                operator: In
                values:
                - linux

    # if using Robusta's embedded kube-prometheus-stack, you can configure the Prometheus Operator's components with nodeAffinities too
    kube-prometheus-stack:
      alertmanager:
        alertmanagerSpec:
          affinity:
            nodeAffinity: ... # copy from above
      prometheus:
        prometheusSpec:
          affinity:
            nodeAffinity: ... # copy from above
      prometheusOperator:
        affinity:
          nodeAffinity: ... # copy from above
        admissionWebhooks:
          deployment:
            affinity:
              nodeAffinity: ... # copy from above
          patch:
            affinity:
              nodeAffinity: ... # copy from above
      kube-state-metrics:
        affinity:
          nodeAffinity: ... # copy from above
      grafana:
        affinity:
          nodeAffinity: ... # copy from above
      thanosRuler:
        thanosRulerSpec:
          affinity:
            nodeAffinity: ... # copy from above


Running Robusta on Nodes with Taints
-------------------------------------------------

To run all the Robusta components on nodes with taints you must add tolerations to each one of them. This includes the Kube Prometheus Stack components if you have ``enablePrometheusStack: true`` in your Helm values file.


Add the following to your Helm values:

.. code-block:: yaml


    globalConfig:
      popeye_job_spec:
        tolerations: ... # Your Toleration
        - key: "appname"
          operator: "Equal"
          value: "robusta"
          effect: "NoSchedule"
      krr_job_spec:
        tolerations:
        - key: "appname"
          operator: "Equal"
          value: "robusta"
          effect: "NoSchedule"
          
    holmes:
      tolerations:  ... # copy from above

    runner:
      tolerations:  ... # copy from above

    kubewatch:
      tolerations:  ... # copy from above


    kube-prometheus-stack:

      prometheus:
        prometheusSpec:
          tolerations:  ... # copy from above

      alertmanager:
        alertmanagerSpec:
          tolerations:  ... # copy from above

      prometheusOperator:
        tolerations:  ... # copy from above

        admissionWebhooks:
          deployment:
            tolerations:  ... # copy from above

          patch:
            tolerations:  ... # copy from above

      kube-state-metrics:
        tolerations:  ... # copy from above

      grafana:
        tolerations:  ... # copy from above

      thanosRuler:
        thanosRulerSpec:
          tolerations:  ... # copy from above

General Tips
---------------
To see your node labels, run ``kubectl get nodes --show-labels``
