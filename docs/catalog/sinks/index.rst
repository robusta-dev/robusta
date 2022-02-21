Sinks
======

Playbooks results can be sent to one or more sinks (destinations).

Supported sinks
^^^^^^^^^^^^^^^^^^^^^
The following sinks are supported:

* :ref:`slack`
* `Robusta UI <https://home.robusta.dev/ui/>`_ - send playbooks results to Robusta's web UI
* `MS Teams <https://docs.robusta.dev/master/catalog/sinks/ms-teams.html>`_ - send playbooks results to an MS Teams channel webhook.
* `Kafka <https://docs.robusta.dev/master/catalog/sinks/kafka.html>`_ - send playbooks results to a Kafka topic
* `Datadog <https://docs.robusta.dev/master/catalog/sinks/DataDog.html>`_ - send playbooks results to the Datadog events API
* `OpsGenie <https://docs.robusta.dev/master/catalog/sinks/Opsgenie.html>`_ - send playbooks results to the OpsGenie alerts API
* :ref:`Telegram` - send playbooks results to Telegram group or private conversation
* `Webhook <https://docs.robusta.dev/master/catalog/sinks/webhook.html>`_- send playbooks results to a webhook

**Need support for something not listed here?** `Tell us and we'll add it to the code. <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=feature_request.md&title=New%20Sink:>`_

:ref:`Read the docs on configuring sinks. <Defining additional sinks>`

Formatting data for sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For the most part, playbooks are sink-agnostic. Data will automatically be formatted appropriately for each sink.


Default sinks
-------------
If a playbook doesn't specify a sink then output will be sent to the default sinks. A sink is considered default
if it has the field `default: true` in the YAML.

Sink documentation
^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   slack
   telegram
   kafka
   DataDog
   ms-teams
   webhook
   Opsgenie