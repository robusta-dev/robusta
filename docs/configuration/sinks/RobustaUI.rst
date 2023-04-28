Robusta UI
#################

Robusta can send Kubernetes issues and events in your Kubernetes cluster to the Robusta UI.

Example Output:

    .. image:: /images/robusta-demo.gif
        :width: 1000
        :align: center

To configure Robusta UI, use our CLI to generate a token. Run:

.. code-block::
   :name: cb-robusta-ui-sink-generate-token

    robusta integrations ui


Configuring the Robusta UI sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: bash
      :name: cb-robusta-ui-sink-config

        sinksConfig:
            - robusta_sink:
                name: robusta_ui_sink
                token: <your-token>
                ttl_hours: 4380

.. note::

    **Inactive** Robusta clusters have a default 6 months **data retention** span (4380 hours).

   To prevent short-lived clusters from fililng up the UI, you can remove clusters that haven't communicated for more than a few hours by setting ``ttl_hours = <number-time-span>``.

Save the file and run

.. code-block:: bash
   :name: cb-add-victorops-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

**Example Output:**

For full overview of Robusta UI features check our `home page <https://home.robusta.dev>`_.

.. image:: /images/robusta-ui-example.png
    :width: 1000
    :align: center
