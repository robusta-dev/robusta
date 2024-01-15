Google Chat
#################

Robusta can report issues and events in your Kubernetes cluster by sending
messages via the Google Chat.

Setting up the Google Chat integration
------------------------------------------------

All you need to set up Google Chat sink for Robusta is to enable a webhook
for a certain Google Chat Space. This essentially means that an administrator
of the chat has to extract a special URL for this Chat Space that enables
the integration. You can find out more about webhook URLs in the Google
documentation, for example <here|https://developers.google.com/chat/how-tos/webhooks>

Configuring the Google Chat sink in Robusta
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - google_chat_sink:
            name: gchat_sink
            webhook_url: https://chat.googleapis.com/v1/spaces/space-id/messages?key=xyz&token=pqr


Then do a :ref:`Helm Upgrade <Simple Upgrade>`.
