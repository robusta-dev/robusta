ServiceNow
#################

Robusta can report issues and events in your Kubernetes cluster by creating
issues in ServiceNow.

.. image:: /images/servicenow_image.png
  :width: 600
  :align: center

Configuring the ServiceNow Sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - service_now_sink:
            name: robusta_integration
            instance: serviceNow_id
            username: admin
            password: SecurePassword@123
            caller_id: robusta_bot

* ``instance``: Your ServiceNow instance identifier.
* ``caller_id`` (optional): Used to specify a user for the "Caller" field in ServiceNow incidents. If not set, this field defaults to "(empty)". It's advisable to create a dedicated user, like "robusta_bot", to easily track incidents from Robusta.


Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

.. note::

   To secure your username and password using Kubernetes Secrets, see :ref:`Managing Secrets`.
