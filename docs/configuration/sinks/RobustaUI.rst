Robusta UI
#################

Robusta can send issues and events in your Kubernetes cluster to the `Robusta UI <https://home.robusta.dev/>`_.

.. image:: /images/robusta-ui.gif
  :align: center


Configuring the Robusta UI Sink
------------------------------------------------

Use the ``robusta`` CLI to generate a token:

.. code-block::
   :name: cb-robusta-ui-sink-generate-token

    robusta integrations ui

Add a new sink to your Helm values, under ``sinksConfig``, with the token you generated:

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: bash
      :name: cb-robusta-ui-sink-config

        sinksConfig:
        - robusta_sink:
            name: robusta_ui_sink
            token: <your-token>
            ttl_hours: 4380

Perform a :ref:`Helm Upgrade <Simple Upgrade>`.

Handling Short-Lived Clusters in the UI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, inactive Robusta clusters will be kept in the UI for 6 months **data retention**. (4380 hours)

If you have many short-lived clusters, you can remove them from the UI automatically once they stop running.
To do so, configure a shorter retention period by setting the ``ttl_hours`` in the Robusta UI sink settings:

.. code-block:: bash
  :name: cb-robusta-ui-sink-config

  sinksConfig:
  - robusta_sink:
      name: robusta_ui_sink
      token: <your-token>
      # automatically clean up old clusters in the UI if they are disconnected 12+ hours
      ttl_hours: 12

More Information about the UI
-------------------------------------
For more information on UI features, view `robusta.dev <https://home.robusta.dev>`_.
