Deploying to Specific Nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can run Robusta on specific nodes in your cluster. For example, on a hybrid Windows and Linux cluster, you'll want
to ensure Robusta runs on Linux nodes.

You can configure this using either ``nodeSelectors`` or ``affinities``.

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

General Tips
---------------
To see your node labels, run ``kubectl get nodes --show-labels``
