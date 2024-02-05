ServiceNow
#################

Robusta can report issues and events in your Kubernetes cluster by creating
issues in ServiceNow.

Configuring the ServiceNow sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - service_now_sink:
            name: some_name
            instance: abcd123
            username: admin
            password: blah-blah
            caller_id: robusta

.. note::

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

All the fields except for caller_id are required. caller_id is the optional id of a
user in ServiceNow that will be used for the "Caller" field/column for incidents.
If it's not set, ServiceNow will set this field to "(empty)". It might be useful to
create a separate user, named for example "Robusta", to keep track of which incidents
are being created by Robusta.