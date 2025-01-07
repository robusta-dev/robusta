Route By Time of Day
####################

In this example we'll route alerts to different support teams based on the time of day:

* Between 12AM and 12PM, #shift-1 will receive alerts.
* The rest of the time, #payment-support-2 will recieve notifications.

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: shift_1_sink
        slack_channel: shift-1
        api_key: secret-key
        activity:
            timezone: UTC
            intervals:
            - days: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            hours:
            - start: 00:00  # 12 AM
                end: 12:00  # 12 PM

    - slack_sink:
        name: shift_2_sink
        slack_channel: shift-2
        api_key: secret-key
        activity:
            timezone: UTC
            intervals:
            - days: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            hours:
            - start: 12:00  # 12 PM
                end: 23:59  # 11:59 PM

For more information on time-based routing, view :ref:`Route by Time`.
