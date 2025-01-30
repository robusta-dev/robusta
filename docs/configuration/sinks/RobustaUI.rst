Robusta UI
#################

Take your Kubernetes monitoring to the next level with a Robusta UI integration:

- **AI Assistant**: Solve alerts faster with an AI assistant that highlights relevant observability data
- **Alert Timeline**: View Prometheus alerts across multiple clusters and spot correlations with a powerful timeline view
- **Change Tracking**: Correlate alerts with changes to your infrastructure or applications, with Robusta’s automatic change tracking for Kubernetes

.. raw:: html

    <div style="text-align: center;">
      <a href="https://www.loom.com/share/89c7e098d9494d79895738e0b06091f0" target="_blank" rel="noopener noreferrer">
          <img src="https://cdn.loom.com/sessions/thumbnails/89c7e098d9494d79895738e0b06091f0-f508768968f50b46-full-play.gif">
      </a>
    </div>


Configuring the Robusta UI Sink
------------------------------------------------

.. tip::
    This guide is for users who have already installed Robusta on their cluster. If you haven't installed Robusta yet, we recommend starting by `creating a free Robusta UI account ↗ <https://platform.robusta.dev/signup?utm_source=docs&utm_content=robusta-ui-sink-page>`_ instead.

Use the ``robusta`` CLI to generate a token:

.. code-block::
   :name: cb-robusta-ui-sink-generate-token

    robusta integrations ui

Add a new sink to your Helm values (``generated_values.yaml``), under ``sinksConfig``, with the token you generated:

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
