Robusta UI
#################

Robusta can send Playbooks results to Robusta UI.

To configure Robusta UI, use our CLI to generate a token. Run:

.. code-block:: cb-robusta-ui-sink-generate-token

    robusta integrations ui


Configuring the Robusta UI sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: cb-robusta-ui-sink-config

        sinksConfig:
            - robusta_sink:
                name: robusta_ui_sink
                token: <your-token>
                ttl_hours: 4380

.. note::

    | **Unactive** Robusta clusters have a default 6 months **data retention** span (4380 hours).
    | For Test or ephemeral clusters you can use a custom data retention span using ``ttl_hours = <number-time-span>``.

Save the file and run

.. code-block:: bash
   :name: cb-add-victorops-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

**Example Output:**

For full overview of Robusta UI features check our `home page <https://home.robusta.dev>`_.

.. image:: /images/robusta-ui-example.png
    :width: 1000
    :align: center
