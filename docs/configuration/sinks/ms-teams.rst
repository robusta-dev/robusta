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

- Click '...' on the channel you want to add the webhook to.
- Click 'Workflows'.
- In the search box type 'webhook'.
- Select ``webhook template``.
- Name the webhook as 'Robusta Webhook'.
- Click 'Next'.
- Make sure the right Team & Channel is selected
- Click 'Add workflow'.
- Copy the ``webhook_url``.

.. image:: /images/msteams_sink/msteam_get_webhook_url.gif
    :width: 1024
    :align: center


Dynamically Route MS Teams Alerts
-------------------------------------------------------------------

You can set the MS Teams webhook url value dynamically, based on the value of a specific ``annotation`` and environmental variable passed to runner.

This can be done using the optional ``webhook_override`` sink parameter.

As for now, the ``webhook_override`` parameter supports retrieving values specifically from annotations. You can specify an annotation key to retrieve the MS Teams webhook URL using the format ``annotations.<annotation_key>``. For example, if you use ``annotations.ms-team-alerts-sink``, the webhook URL will be taken from an annotation with the key ``ms-team-alerts-sink``.

If the specified annotation does not exist, the default webhook URL from the ``webhook_url`` parameter will be used. If the annotation exists but does not contain a URL, the system will look for an environmental variable with the name matching the ``annotation`` value.

.. code-block:: yaml

     sinksConfig:
     # MS Teams integration params
    - ms_teams_sink:
        name: main_ms_teams_sink
        webhook_url: teams-incoming-webhook  # see instructions below
        webhook_override: "annotations.ms-team-alerts-sink"

A replacement pattern is also allowed, using ``$`` sign, before the variable.
For cases where labels or annotations include special characters, such as ``${annotations.kubernetes.io/service-name}``, you can use the `${}` replacement pattern to represent the entire key, including special characters.
For example, if you want to dynamically set the MS Teams webhook url based on the annotation ``kubernetes.io/service-name``, you can use the following syntax:

- ``webhook_override: "${annotations.kubernetes.io/service-name}"``

Example:

.. code-block:: yaml

        sinksConfig:
        - ms_teams_sink:
            name: main_ms_teams_sink
            webhook_url: teams-incoming-webhook  # see instructions below
            webhook_override: ${annotations.kubernetes.io/service-name}

Redirect to Platform
-------------------------------------------------------------------

By default, MS Teams notifications include buttons to view more information in the Robusta SaaS platform.
If you don't use Robusta SaaS you can modify these links to point at Prometheus instead.
To do so, set prefer_redirect_to_platform: false.

For example:

.. code-block:: yaml

     sinks_config:
     - ms_teams_sink:
        name: main_ms_teams_sink
        webhook_url: teams-incoming-webhook
        prefer_redirect_to_platform: false