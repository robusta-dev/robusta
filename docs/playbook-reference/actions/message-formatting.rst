Message Formatting
########################

These actions are useful for creating notifications or customising the output of existing actions.

To control where these notifications are sent, refer to :ref:`sinks-overview`.

Create finding
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.common_actions.create_finding on_job_failure

.. robusta-action:: playbooks.robusta_playbooks.event_enrichments.create_event_finding on_event_create

Finding attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.common_actions.customise_finding on_pod_crash_loop
