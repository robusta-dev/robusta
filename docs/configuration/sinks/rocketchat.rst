Rocket.Chat
#################

.. admonition:: This page documents a legacy sink in Robusta classic
   :class: warning

   For new setups, we recommend `HolmesGPT <https://holmesgpt.dev/>`_ instead.

   Sinks statically forward every notification to a fixed destination. Modern Robusta instead investigates and routes alerts **agentically** so the LLM makes intelligent triage decisions about each alert. Set this up with :ref:`triggered workflows <defining-playbooks>` and `MCP servers <https://holmesgpt.dev/data-sources/remote-mcp-servers/?tab=robusta-helm-chart>`_, or configure `alert triage <https://platform.robusta.dev/holmes/alerts-triage>`_ in the Robusta platform.


Robusta can report issues and events in your Kubernetes cluster to Rocket.Chat.

.. image:: /images/rocketchat1.png
  :width: 600


Prerequisites
------------------------------------------------

Before you begin setting up the Rocket.Chat sink, ensure you have the following information ready:

* Server URL
* Personal Access Token
* User ID
* Channel name

**Rocket.Chat Server Setup**

First, you need to set up a Rocket.Chat server. If you haven't done this yet, you can find detailed information on deploying on-prem servers at the following URL: `Rocket.Chat Installation Guide <https://www.rocket.chat/install>`_.

Or if you prefer using RocketChat's cloud SaaS platform, you can follow the instructions at this URL: `Rocket.Chat Cloud Setup <https://cloud.rocket.chat>`_.

**Generating Personal Access Token and User ID**

Follow these steps to generate the required `Personal Access Token` and `User ID`:

1. Log in to your Rocket.Chat server using your valid username and password.

2. Click on your avatar and select `My Account` from the menu.

3. Navigate to `Profile` > `Personal Access Tokens`.

4. Check the `Ignore Two Factor Authentication` option if enabled.

5. Fill in the `Add new Personal Access Token` text field and click the `Add` button.

6. Copy the provided `Personal Access Token` and `User ID` for later use.


.. image:: /images/rocketchat2.png
  :width: 1000

Configuring the Rocket.Chat sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

         sinksConfig:
         # Rocket.Chat integration params
        - rocketchat_sink:
              name: main_rocketchat_sink
              user_id: <User ID>
              channel: <Rocket.Chat channel>
              token: <Personal Access Token>
              server_url: <Server URL>

Save the file and run

.. code-block:: bash
   :name: cb-add-rocketchat-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

