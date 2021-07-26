Scheduled Playbooks
############################

Scheduling Overview
-------------------
| Robusta playbooks can be scheduled and run periodically.
| Similarly to other playbooks, there's also a trigger.
| In this case it's a recurring trigger.

Trigger Details
-------------------

| In order to define the recurring trigger, use the ``@on_recurring_trigger(seconds_delay=None, repeat=-1)``
| Using this trigger, the playbook will be executed every ``second_delay`` seconds, for ``repeat`` times.


| **Trigger Parameters:**
| **seconds_delay -** The seconds delay between executions.
| **repeat -** The number of time the scheduler will run the playbook. Specifying ``repeat=-1`` means the scheduler will tun the playbook forever.


Scheduled Playbook Example
------------------------------

| First, we'll implement our playbook's code:
| In the playbooks folder, add a file named: ``my_scheduled_playbook.py``
| Edit it, and add the following:

.. code-block:: python

    from robusta.api import *

    class MyScheduledPlaybookParams(BaseModel):
        some_string_param: str

    @on_recurring_trigger(seconds_delay=None, repeat=-1)
    def my_scheduled_playbook(event: RecurringTriggerEvent, action_params: MyScheduledPlaybookParams):
        # implement any python logic here
        logging.info(f"My scheduled playbook running {action_params.some_string_param}")


| Now, configure the playbook in the ``active_playbooks.yaml`` :

.. code-block:: yaml

    active_playbooks:
      - name: "my_scheduled_playbook"
        trigger_params:
          repeat: 10
          seconds_delay: 20
        action_params:
          some_string_param: "Scheduled Playbook - Hello World"

| Lastly, deploy the playbook: ``robusta playbooks deploy playbooks``
| That's it!
| Now, this playbook will run every ``20`` seconds for ``10`` times.
| In the robusta-runner logs, you'll be able to see the log line printed on each execution.
