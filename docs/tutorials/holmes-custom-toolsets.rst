Adding Toolsets to Holmes
#########################

Holmes allows you to define custom toolsets that enhance its functionality by enabling additional tools to run Kubernetes commands or other tasks.

In this guide, we will show how to add a custom toolset to Holmes in your ``generated_values.yaml`` file.

Updating the Helm Values (``generated_values.yaml``)
----------------------------------------------------

To add a toolset in Holmes, update the ``generated_values.yaml`` with the following configuration:

.. code-block:: yaml

    enableHolmesGPT: true
    holmes:
      additionalEnvVars:
        - name: ROBUSTA_AI
          value: "true"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: holmes-secrets
              key: openAiKey
      toolsets:
        # Define the custom toolset (example: "switch_clusters")
        - name: "switch_clusters"
          prerequisites:
            - command: "kubectl version --client"
          tools:
            - name: "switch_cluster"
              description: "Used to switch between multiple Kubernetes contexts (clusters)"
              command: "kubectl config use-context {{ cluster_name }}"

- **``toolsets``**: Defines a custom toolset, in this case, a ``switch_clusters`` toolset that allows Holmes to switch between Kubernetes clusters using ``kubectl``. The toolset includes a tool called ``switch_cluster``, which accepts the ``cluster_name`` as input and runs the corresponding ``kubectl`` command.

Applying the Changes
--------------------

Once you have updated the ``generated_values.yaml`` file, apply the changes by running the Helm upgrade command:

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>

After the deployment, the custom toolset is automatically available for Holmes to use. Holmes will now be able to run the ``switch_cluster`` tool whenever required, allowing it to switch between Kubernetes contexts based on the defined parameters.
