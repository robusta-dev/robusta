Scheduled
############################

.. _on_schedule:

Robusta can run actions on a schedule. Schedules come in two forms:

Fixed delay
----------------------

These triggers run with a fixed delay between each invocation. For example:

.. code-block:: yaml

    triggers:
    - on_schedule:
        fixed_delay_repeat:
          repeat: 10             # number of times to run or -1 to run forever
          seconds_delay: 60      # seconds between each run

The trigger will fire for the first time 120 seconds after the playbook is first configured.

Dynamic delay
----------------------

These triggers run with a different delay between each invocation. For example, the following will run 3 times with
a delay of 150 seconds the first time, 160 the second, and 170 the third.

.. code-block:: yaml

    triggers:
    - on_schedule:
        dynamic_delay_repeat:
          delay_periods: [150, 160, 170]

The first delay cannot be less than 120 seconds. If you define less, 120 seconds will be used instead.


Cron based
----------------------

If you want to run a playbook on a `cron schedule <https://crontab.guru/>`_, you can use the following:

.. code-block:: yaml

    triggers:
    - on_schedule:
        cron_schedule_repeat:
          cron_expression: "0 12 * * 1" # every Monday at 12:00

If the first run should be in less than 120 seconds, the trigger will fire 120 seconds after the playbook is first configured.
