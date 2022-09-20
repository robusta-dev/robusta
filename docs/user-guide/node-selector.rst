Deploying Robusta on specific nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Additional configurations can be added to specify which nodes you would like for Robusta to run on by using ``nodeSelectors`` or ``affinity``.
The ``nodeSelector`` or ``affinity`` chosen should be configured for both runner and forwarder (kubewatch).

The following configuration is an example that will cause Robusta's pods to only be scheduled on nodes running linux.
Our ``nodeSelector`` checks if node has a label ``kubernetes.io/os`` that has the value ``linux``.

.. code-block:: yaml

    runner:
      nodeSelector:
        kubernetes.io/os: linux

    kubewatch:
      nodeSelector:
        kubernetes.io/os: linux

Additionally we also support affinities in our pods, you can select a node in a similar way using nodeAffinities.

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

For a list of all the current labels and values you have on your nodes run ``kubectl get nodes --show-labels``

