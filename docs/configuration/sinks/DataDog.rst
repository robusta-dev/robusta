DataDog
##########

Robusta can report issues and events in your cluster to the Datadog events API.

Example Output:

    .. image:: /images/deployment-babysitter-datadog.png
        :width: 1000
        :align: center

To configure datadog sink, we need a DataDog API key. The API key can be retrieved from your DataDog Account.

Configuring the Datadog sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - datadog_sink:
            name: datadog_sink
            api_key: "datadog api key"

Save the file and run

.. code-block:: bash
   :name: cb-add-discord-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

Using Environment Variables for API Keys
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

   runner:
     additional_env_vars:
       - name: DATADOG_API_KEY
         valueFrom:
           secretKeyRef:
             name: robusta-secrets
             key: datadog_key

   sinksConfig:
     - datadog_sink:
         name: datadog_sink
         api_key: "{{ env.DATADOG_API_KEY }}"

For more information, see :ref:`Managing Secrets`.
