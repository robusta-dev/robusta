Scheduled
############################

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
a delay of 10 seconds the first time, 20 the second, and 25 the third.

.. code-block:: yaml

    triggers:
    - on_schedule:
        dynamic_delay_repeat:
          delay_periods: [10, 20, 25]

The first delay cannot be less than 120 seconds. If you define less, 120 seconds will be used instead.