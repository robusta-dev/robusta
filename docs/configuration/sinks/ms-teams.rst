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
            webhook_override: DYNAMIC MS TEAMS WEBHOOK URL OVERRIDE (Optional)

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Obtaining a webhook URL
-----------------------------------

- Choose a channel and click "Manage Channel".
- Click "Connectors->Edit", and configure an "Incoming Webhook"
- Fill out the name ``robusta``.
- Optional: upload the :download:`robusta logo </images/msteams_sink/msteams_robusta_logo.png>` for the connector’s image.
- Copy the ``webhook_url``.

.. image:: /images/msteams_sink/msteam_get_webhook_url.gif
    :width: 1024
    :align: center


Dynamic MS Teams Webhook Override
-------------------------------------------------------------------

You can set the ``MS Teams`` webhook url value dynamically, based on the value of a specific ``annotation`` and environmental variable passed to runner.

This can be done using the optional ``webhook_override`` sink parameter.

As for now we support only getting values for annotations, the allowed values for this parameter are:

- ``annotations.anno`` - The ``MS Teams`` webhook URL will be taken from an annotation with the key anno.
If no such annotation exists, the default webhook will be used. If the annotation is found but its value
does not contain a valid URL, the system will search for an environmental variable with the name of the value
 in the ``additional_env_vars`` section of your ``generated_values.yaml`` file.

For example:

.. code-block:: yaml

     sinksConfig:
     # MS Teams integration params
    - ms_teams_sink:
        name: main_ms_teams_sink
        webhook_url: teams-incoming-webhook  # see instructions below
        webhook_override: DYNAMIC MS TEAMS WEBHOOK URL OVERRIDE (Optional)

A replacement pattern is also allowed, using ``$`` sign, before the variable.
For cases where labels or annotations include special characters, such as ``${annotations.kubernetes.io/service-name}``, you can use the `${}` replacement pattern to represent the entire key, including special characters.
For example, if you want to dynamically set the MS Teams webhook url based on the annotation ``kubernetes.io/service-name``, you can use the following syntax:

- ``webhook_override: "${annotations.kubernetes.io/service-name}"``
