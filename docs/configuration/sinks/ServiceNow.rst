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
* ``caller_id`` (optional): The ID of a user in ServiceNow to be used for the "Caller" field/column for incidents. Leaving this field unset will result in ServiceNow setting this field to "(empty)". Consider creating a separate user, such as "robusta_bot", to track incidents created by Robusta.


Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.
