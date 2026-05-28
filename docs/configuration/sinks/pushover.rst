Pushover
#################

Robusta can report issues and events in your Kubernetes cluster to Pushover notification enabled devices.

.. note::
    Pushover only supports sending images as attachments, no videos or log files. As a workaround,
    Robusta sends log files as message content to Pushover. Pushover has a 1024 character message limit,
    meaning that some log messages may be cut off.

Getting your User key
------------------------------------------------
Login on `Pushover <https://pushover.net>`_ to grab your User key, which should be displayed on the right.

Obtaining your API token
------------------------------------------------
First, create an Application `here <https://pushover.net/apps/build>`_. This should prompt you with an API key which you can use in your Helm values.

If you ever forget your API token, head over to `Pushover <https://pushover.net>`_ and scroll to the bottom of the page after logging in. Your Application will be there, containing the API token.

Configuring the Pushover sink
------------------------------------------------
Now we're ready to configure the Pushover sink.

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - pushover_sink:
            name: pushover_sink
            token: <YOUR_API_TOKEN>
            user: <YOUR_USER_KEY>
            device: <DEVICE_IN_PUSHOVER> # (Optional) If not set, will push to all Pushover enabled devices
            send_files: true # (Optional - Default is true) Whether to send images and log messages to Pushover
            send_as_html: true # (Optional - Default is true) Whether you want to send Robustas messages as parsable HTML to Pushover
            pushover_url: <CUSTOM_PUSHOVER_URL> # (Optional) Defaults to https://api.pushover.net/1/messages.json
.. note::

    If you don't want Robusta to send file images and log messages, set ``send_files`` to ``False`` in your Pushover sink. (True by default)

Save the file and run

.. code-block:: bash
   :name: cb-add-pushover-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

.. note::

   To secure your API token and user key using Kubernetes Secrets, see :ref:`Managing Secrets`.

You should now get playbook results in Pushover!
