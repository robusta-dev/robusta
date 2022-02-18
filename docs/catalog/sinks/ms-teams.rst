MS teams
##########

Robusta can send playbook result to a MS teams channel webhook.

To configure a MS teams sink we need a webhook URL for the target teams channel. You can configure it in MS teams channel connectors.

Configuring the MS teams sink
------------------------------------------------

.. admonition:: values.yaml

    .. code-block:: yaml

        sinks_config:
        - ms_teams_sink:
            name: main_ms_teams_sink
            webhook_url: teams channel incoming webhook  # configured using teams channel connectors

**Example Output:**

    .. image:: /images/deployment-babysitter-teams.png
      :width: 600
      :align: center
