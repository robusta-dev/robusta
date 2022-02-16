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

Dynamic delay
----------------------

These triggers run with a different delay between each invocation. For example, the following will run 3 times with
a delay of 10 seconds the first time, 20 the second, and 25 the third.

.. code-block:: yaml

    triggers:
    - on_schedule:
        dynamic_delay_repeat:
          delay_periods: [10, 20, 25]

