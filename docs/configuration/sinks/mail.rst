Mail
#################

Robusta can report issues and events in your Kubernetes cluster by sending
emails.

Connecting the mail sink
------------------------------------------------

To set up the mail sink, you need access to an SMTP server. You should also
set the sender and receiver(s) addresses.

Robusta uses `Apprise library <https://github.com/caronc/apprise>`_ under the hood for running mail
notifications. You can configure the "mailto" field described below using
the convenient and sophisticated syntax provided by Apprise. For more details
`see here <https://github.com/caronc/apprise/wiki/Notify_email>`_.

.. image:: /images/mail_sink1.png
  :width: 640

Configuring the mail sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - mail_sink:
            name: mail_sink
            mailto: "mailtos://user:password@server&from=a@x&to=b@y,c@z"
            with_header: false  # optional

The default value of the optional `with_header` parameter is `true`. If set to `false`, mails
sent by this sink will *not* include header information, such as the finding header, investigate
button and the source of the notification.

.. note::

    We highly recommend using the quotes around "mailto" to ensure special characters are handled correctly.

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.
