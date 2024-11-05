Common Examples
===================================

Here are examples of common routing patterns that teams use with Robusta. The goal is to send each team only the most relevant alerts.

Use Case 1: Route Specific Alerts to Seperate Teams and Slack Channels
**********************************************************************************
In this example we are going to consider two teams, with #frontend and #backend channels. The Frontend team should only receive alerts that are from the Frontend namespace. All the alerts from backend namespace should go to the #backend channel


.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: frontend_sink
        slack_channel: frontend-notifications
        api_key: secret-key
        scope:
            include:
            - namespace: [frontend]

    - slack_sink:
        name: backend_sink
        slack_channel: backend-notifications
        api_key: secret-key
        scope:
            include:
            - namespace: [backend]

For a complete list of filters, view the :ref:`Scopes documentation <sink-scope-matching>`.

Use Case 2: Route Alerts To Different Support Teams Based On Time Of The Day
**********************************************************************************

Let's see how we can route alerts between two teams with different Slack channels. Between 12AM to 12 PM #payments-support-1 should receive alerts. The rest of the time #payment-support-2 should recieve notifications.

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: payments_support_1_sink
        slack_channel: payments-support-1
        api_key: secret-key
        activity:
            timezone: UTC
            intervals:
            - days: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            hours:
            - start: 00:00  # 12 AM
                end: 12:00  # 12 PM

    - slack_sink:
        name: payments_support_2_sink
        slack_channel: payments-support-2
        api_key: secret-key
        activity:
            timezone: UTC
            intervals:
            - days: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            hours:
            - start: 12:00  # 12 PM
                end: 23:59  # 11:59 PM


For more information on time-based routing, :ref:`view <Route by Time>`

If you want to selectively apply time-based-routing to certain alerts only, then this method can be combined with :ref:`Scopes <sink-scope-matching>`. For example:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: payments_support_1_sink
        slack_channel: payments-support-1
        api_key: secret-key
        activity:
            timezone: UTC
            intervals:
            - days: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            hours:
            - start: 00:00  # 12 AM
                end: 12:00  # 12 PM
        scope:
            include:
            - namespace: [payment, renewal]

    - slack_sink:
        name: payments_support_2_sink
        slack_channel: payments-support-2
        api_key: secret-key
        activity:
            timezone: UTC
            intervals:
            - days: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            hours:
            - start: 12:00  # 12 PM
                end: 23:59  # 11:59 PM
        scope:
            include:
            - namespace: [payment, renewal]