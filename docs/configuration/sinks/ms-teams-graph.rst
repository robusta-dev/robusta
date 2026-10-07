MS Teams (Graph API)
#####################

.. admonition:: This page documents a sink in Robusta classic
   :class: warning

   For new setups, we recommend `HolmesGPT <https://holmesgpt.dev/>`_ instead.

   HolmesGPT triages your alerts instead of just forwarding them. Sinks are deterministic: they send every notification, unchanged, to a fixed destination, leaving you to read and prioritize each one yourself.

   HolmesGPT instead uses AI to investigate each alert, surface the likely root cause, and escalate only what needs attention — so you get fewer, more actionable notifications. Set this up with `Alerts Triage <https://platform.robusta.dev/holmes/alerts-triage>`_ for alerts, or :ref:`Triggered Workflows <defining-playbooks>` for custom events.

Robusta can post notifications to MS Teams channels with the `Microsoft Graph API <https://learn.microsoft.com/en-us/graph/api/channel-post-messages>`_,
as an Adaptive Card. Unlike the :doc:`webhook based MS Teams sink <ms-teams>`, a single sink can post to any channel
of any team the sending user belongs to, and route each notification to a channel based on labels and annotations.

.. note::

    2-way interactivity (``CallbackBlock``) isn't implemented yet.

How it authenticates
------------------------------------------------

Microsoft Graph only allows posting channel messages with *delegated* permissions (on behalf of a user).
The sink signs in as a dedicated service user with the OAuth2 Resource Owner Password Credentials (ROPC) flow,
and messages are posted as that user.

1. In the Entra ID admin center, create an **App registration** (single tenant).
2. Under **API permissions**, add the Microsoft Graph *delegated* permission ``ChannelMessage.Send``, and grant admin consent.
3. Under **Certificates & secrets**, create a client secret (or enable **Allow public client flows** under **Authentication** and leave ``client_secret`` empty).
4. Create a service user, for example ``robusta-alerts@yourcompany.onmicrosoft.com``. ROPC does not support interactive MFA,
   so exclude this user from MFA / Conditional Access policies that require it.
5. Add the service user as a member of every team Robusta should post to.

Get the team and channel ids
------------------------------------------------

In Teams, click **...** next to the channel, then **Get link to channel**. The link looks like:

.. code-block:: text

    https://teams.microsoft.com/l/channel/19%3Aabc123%40thread.tacv2/Alerts?groupId=<TEAM_ID>&tenantId=<TENANT_ID>

- ``groupId`` is the team id.
- The part after ``/channel/`` is the channel id. It can be used as is (URL-encoded) or decoded (``19:abc123@thread.tacv2``).

Configuring the sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - ms_teams_graph_sink:
            name: teams_graph_sink
            tenant_id: <TENANT_ID>
            client_id: <APP_CLIENT_ID>
            client_secret: "{{ env.TEAMS_CLIENT_SECRET }}"
            username: robusta-alerts@yourcompany.onmicrosoft.com
            password: "{{ env.TEAMS_PASSWORD }}"
            team_id: <TEAM_ID>
            channel_id: "19:abc123@thread.tacv2"

        runner:
          additional_env_vars:
          - name: TEAMS_CLIENT_SECRET
            valueFrom:
              secretKeyRef:
                name: teams-graph-credentials
                key: client_secret
          - name: TEAMS_PASSWORD
            valueFrom:
              secretKeyRef:
                name: teams-graph-credentials
                key: password

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Configuration parameters
------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Field
     - Default
     - Description
   * - ``tenant_id``
     - *(required)*
     - Entra ID tenant id.
   * - ``client_id``
     - *(required)*
     - App registration (client) id.
   * - ``client_secret``
     - *(none)*
     - App registration client secret. Leave empty for a public client app.
   * - ``username`` / ``password``
     - *(required)*
     - The service user Robusta signs in as and posts as.
   * - ``team_id``
     - *(required)*
     - Default team id.
   * - ``channel_id``
     - *(required)*
     - Default channel id, in ``team_id``.
   * - ``channel_override``
     - *(none)*
     - Template resolved against the finding subject labels/annotations to route to a different channel.
   * - ``namespace_channel_override``
     - *(none)*
     - Template resolved against the finding namespace's labels/annotations to route to a different channel.
   * - ``send_to_default_if_missing``
     - ``true``
     - When an override is configured but doesn't resolve, send to the default channel (``true``) or drop the notification (``false``).
   * - ``send_files``
     - ``true``
     - Include files: text files (e.g. logs) are shown in the card, images are attached to the message.
   * - ``disable_platform_links``
     - ``false``
     - When ``true``, omits the Robusta platform ``Investigate`` and ``Silence`` buttons.
   * - ``oauth_scope``
     - ``<graph_endpoint>/.default``
     - OAuth scope requested for the token.
   * - ``authority_host`` / ``graph_endpoint``
     - ``https://login.microsoftonline.com`` / ``https://graph.microsoft.com``
     - Change for national clouds, e.g. ``https://login.microsoftonline.us`` and ``https://graph.microsoft.us``.

Dynamic Channel Routing
------------------------------------------------

The sink routes each notification with two optional override fields, evaluated in order:

1. ``namespace_channel_override`` — resolved against the **Namespace** object's labels and annotations,
   looked up by the finding's namespace. Skipped for findings without a namespace (e.g. node alerts).
2. ``channel_override`` — resolved against the finding's **subject** labels and annotations
   (for Prometheus alerts, the alert labels and annotations). Same behavior as Slack's ``channel_override``.

If neither produces a channel, ``send_to_default_if_missing`` decides whether the notification goes to the default
channel or is dropped.

The resolved value can be:

- a channel id (``19:abc123@thread.tacv2``, or URL-encoded), posted in ``team_id``, or
- ``<team_id>/<channel_id>``, to post in another team.

Both override fields use the same template syntax as Slack:

- ``cluster_name`` — the Robusta cluster name.
- ``labels.foo`` / ``$labels.foo`` — value of a label.
- ``annotations.bar`` / ``$annotations.bar`` — value of an annotation.
- ``${labels.foo-bar}`` / ``${annotations.example.com/teams-channel}`` — bracket form, required when the key contains
  characters other than letters, digits, or underscores (e.g. ``-``, ``/``, ``.``).
- Composite patterns are allowed: ``"19:$labels.team@thread.tacv2"``.

.. note::

    Kubernetes label values can't contain ``:`` or ``@``, so a channel id can't be stored in a Kubernetes label.
    Use an annotation for Kubernetes objects. Prometheus alert labels can hold channel ids.

Example — route by a namespace annotation, then by an alert label, drop if neither is set:

.. code-block:: yaml

    sinksConfig:
    - ms_teams_graph_sink:
        name: teams_graph_sink
        # ... credentials, team_id and channel_id as above
        namespace_channel_override: "${annotations.example.com/teams-channel}"
        channel_override: "${labels.teams_channel}"
        send_to_default_if_missing: false

.. code-block:: yaml

    apiVersion: v1
    kind: Namespace
    metadata:
      name: payments
      annotations:
        example.com/teams-channel: "19:abc123@thread.tacv2"
