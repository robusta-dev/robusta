Mail
#################

Robusta can report issues and events in your Kubernetes cluster by sending
emails.

Connecting the mail sink
------------------------------------------------

To set up the mail sink, you need access to an SMTP server. You should also
set the sender and receiver(s) addresses.

As Robusta uses the `Apprise library <https://github.com/caronc/apprise>`_ under the hood for running mail
notifications, you can configure the "mailto" field described below using
the convenient and sophisticated syntax provided by Apprise. For more details
`see here <https://github.com/caronc/apprise/wiki/Notify_email>`_.

Configuring the mail sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - mail_sink:
            name: mail_sink
            mailto: "mailtos://user:password@server&from=a@x&to=b@y,c@z"

(Note the quotes around the value in mailto. It's highly recommended to add
them as this ensures that characters like `:` are handled correctly)

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.
