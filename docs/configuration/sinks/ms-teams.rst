MS Teams
##########

Robusta can report issues and events in your Kubernetes cluster to a MS Teams webhook.

.. image:: /images/msteams_sink/deployment-babysitter-teams.png
    :width: 600
    :align: center

To configure a MS Teams sink we need a webhook URL for the target teams channel. You can configure it in MS Teams channel connectors.

Configuring the MS Teams sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - ms_teams_sink:
            name: main_ms_teams_sink
            webhook_url: teams-incoming-webhook  # see instructions below

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Obtaining a webhook URL
-----------------------------------

- Choose a channel and click "Manage Channel".
- Click "Connectors->Edit", and configure an "Incoming Webhook"
- Fill out the name ``robusta``.
- Use the following image for the icon: :download:`download logo </images/msteams_sink/msteams_robusta_logo.png>`.
- Copy the ``webhook_url``.

.. image:: /images/msteams_sink/msteam_get_webhook_url.gif
    :width: 1024
    :align: center
