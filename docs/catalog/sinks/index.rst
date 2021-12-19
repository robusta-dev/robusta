Sinks
======

Playbooks results can be sent to one or more sinks.

Supported sinks
^^^^^^^^^^^^^^^^^^^^^
Currently four sink types are supported:

* :ref:`slack`
* robusta - send playbooks results Robusta's dedicated UI
* kafka - send playbooks results to a Kafka topic
* datadog - send playbooks results to the Datadog events API

Formatting data for sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For the most part, playbooks are sink-agnostic. Data will automatically be formatted appropriately for each sink.

The output from ``resource_babysitter`` looks like this in the different sinks:

**Robusta UI:**

    .. image:: /images/deployment-babysitter-ui.png
      :width: 1000
      :align: center

**Slack:**

    .. image:: /images/deployment-babysitter-slack.png
      :width: 600
      :align: center

**kafka:**

    .. image:: /images/deployment-babysitter-kafka.png
      :width: 400
      :align: center

**Datadog:**

    .. image:: /images/deployment-babysitter-datadog.png
      :width: 1000
      :align: center

Default sinks
-------------
If a playbook doesn't specify a sink then output will be sent to the default sinks. A sink is considered default
if it has the field `default: true` in the yaml.

Current limitations
^^^^^^^^^^^^^^^^^^^^^^^^
The Helm chart only exposes the ability to configure one Robusta sink and one Slack sink. If you want to use capabilities
beyond that, you will have to modify the Helm chart to enable the underlying Robusta features.

Sink documentation
^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   slack
