Google Chat
#################

.. admonition:: This page documents a legacy sink in Robusta classic
   :class: warning

   You probably want `HolmesGPT <https://holmesgpt.dev/>`_ instead.

   Sinks statically forward every notification to a fixed destination. Modern Robusta instead investigates and routes alerts **agentically**, using :ref:`triggered workflows <defining-playbooks>` together with `MCP servers <https://holmesgpt.dev/data-sources/remote-mcp-servers/?tab=robusta-helm-chart>`_, so the LLM makes intelligent triage decisions about each alert instead of blindly forwarding everything.


Robusta can report issues and events in your Kubernetes cluster by sending
messages via the `Google Chat <https://chat.google.com/>`_ app.

.. image:: /images/google-chat-sink.png
  :width: 1000
  :align: center

Prerequisites:
--------------------------

* Chat webhook URL. Find out more about webhook URLs in the Google documentation, `here <https://developers.google.com/chat/how-tos/webhooks>`_

Configuring the Google Chat sink in Robusta
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - google_chat_sink:
            name: gchat_sink
            webhook_url: https://chat.googleapis.com/v1/spaces/space-id/messages?key=xyz&token=pqr


Then do a :ref:`Helm Upgrade <Simple Upgrade>`.
