Mail
#################

Robusta can report issues and events in your Kubernetes cluster by sending
emails using either SMTP servers or Amazon Simple Email Service (SES).

Connecting the mail sink
------------------------------------------------

The mail sink supports two modes:

1. **SMTP Mode** (default): Uses any SMTP server via the `Apprise library <https://github.com/caronc/apprise>`_
2. **Amazon SES Mode**: Uses AWS Simple Email Service for improved reliability and deliverability

SMTP Configuration
------------------------------------------------

To set up SMTP mode, you need access to an SMTP server. You should also
set the sender and receiver(s) addresses.

Robusta uses `Apprise library <https://github.com/caronc/apprise>`_ under the hood for running mail
notifications. You can configure the "mailto" field described below using
the convenient and sophisticated syntax provided by Apprise. For more details
`see here <https://github.com/caronc/apprise/wiki/Notify_email>`_.

.. image:: /images/mail_sink1.png
  :width: 640

.. admonition:: SMTP Configuration - Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - mail_sink:
            name: mail_sink
            mailto: "mailtos://user:password@server&from=a@x&to=b@y,c@z"
            with_header: false  # optional

Amazon SES Configuration
------------------------------------------------

Amazon SES provides better deliverability, detailed analytics, and is often more cost-effective than traditional SMTP servers.

Prerequisites
^^^^^^^^^^^^^

1. **AWS Account**: Set up an AWS account with SES enabled
2. **SES Setup**: Verify sender email addresses in SES console  
3. **IAM Permissions**: Ensure your AWS credentials have ``ses:SendEmail`` and ``ses:SendRawEmail`` permissions
4. **Production Access**: For production use, request SES production access (initially in sandbox mode)

.. admonition:: SES Configuration - Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - mail_sink:
            name: ses_mail_sink
            mailto: "mailtos://alerts@company.com"  # Recipient addresses
            use_ses: true
            aws_region: "us-east-1"
            from_email: "robusta-alerts@company.com"
            with_header: true  # optional
            # Optional: explicit AWS credentials (prefer IAM roles)
            # aws_access_key_id: "${AWS_ACCESS_KEY_ID}"
            # aws_secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
            # configuration_set: "robusta-emails"  # optional

SES Configuration Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Parameter
     - Required
     - Description
   * - ``use_ses``
     - Yes
     - Set to ``true`` to enable SES mode
   * - ``aws_region``
     - Yes
     - AWS region where SES is configured (e.g., ``us-east-1``)
   * - ``from_email``
     - Yes
     - Verified sender email address in SES
   * - ``mailto``
     - Yes
     - Recipient email addresses (same format as SMTP mode)
   * - ``aws_access_key_id``
     - No
     - AWS access key (prefer IAM roles over explicit credentials)
   * - ``aws_secret_access_key``
     - No
     - AWS secret key (prefer IAM roles over explicit credentials)
   * - ``configuration_set``
     - No
     - SES configuration set for tracking and analytics

Authentication Options
^^^^^^^^^^^^^^^^^^^^^^

**Option 1: IAM Roles (Recommended)**

For clusters running in AWS (EKS), use IAM roles for service accounts:

.. code-block:: yaml

    sinksConfig:
    - mail_sink:
        name: ses_mail_sink
        mailto: "mailtos://alerts@company.com"
        use_ses: true
        aws_region: "us-east-1"
        from_email: "robusta@company.com"

**Option 2: Environment Variables**

Set AWS credentials as environment variables:

.. code-block:: bash

    export AWS_ACCESS_KEY_ID="your-access-key"
    export AWS_SECRET_ACCESS_KEY="your-secret-key"

**Option 3: Explicit Configuration**

Include credentials directly in configuration (not recommended for production):

.. code-block:: yaml

    sinksConfig:
    - mail_sink:
        name: ses_mail_sink
        mailto: "mailtos://alerts@company.com"
        use_ses: true
        aws_region: "us-east-1"
        from_email: "robusta@company.com"
        aws_access_key_id: "${AWS_ACCESS_KEY_ID}"
        aws_secret_access_key: "${AWS_SECRET_ACCESS_KEY}"

Multiple Recipients
^^^^^^^^^^^^^^^^^^^

SES mode supports multiple recipients using the same mailto format:

.. code-block:: yaml

    mailto: "mailtos://primary@company.com?to=secondary@company.com,third@company.com"

Common Parameters
------------------------------------------------

The following parameters apply to both SMTP and SES modes:

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Parameter
     - Default
     - Description
   * - ``with_header``
     - ``true``
     - Include finding header, investigate button, and notification source
   * - ``name``
     - Required
     - Unique name for this sink configuration

The default value of the optional `with_header` parameter is `true`. If set to `false`, mails
sent by this sink will *not* include header information, such as the finding header, investigate
button and the source of the notification.

Troubleshooting
------------------------------------------------

**SES Issues**

- **Authentication errors**: Verify AWS credentials and IAM permissions
- **Message rejected**: Check that sender email is verified in SES console
- **Rate limiting**: SES has sending quotas; check your SES console for limits
- **Sandbox mode**: In SES sandbox, you can only send to verified email addresses

**SMTP Issues**

- **Connection errors**: Verify SMTP server details and network connectivity
- **Authentication failures**: Check username/password in mailto URL
- **TLS/SSL issues**: Ensure correct protocol (``mailto://`` vs ``mailtos://``)

.. note::

    We highly recommend using quotes around "mailto" to ensure special characters are handled correctly.

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

.. note::

   To secure your email credentials and AWS credentials using Kubernetes Secrets, see :ref:`Managing Secrets`.