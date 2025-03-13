Manual Triggers
######################################################

Motivation
-------------------------------------------
The main use-case for manual triggers is making troubleshooting easier.

This ties into Robusta's goal of reducing MTTR (mean time to recovery).

Additional use cases are discussed below.

Automation examples
----------------------------------------

Manual actions can be used to automate any repetitive task on Kubernetes:

1. `Run chaos engineering scenarios <https://github.com/robusta-dev/robusta-chaos>`_
2. Stress test pods over HTTP

How it works
----------------------

Internally, troubleshooting actions are implemented the same way as other Robusta actions, like insights and automated
fixes. A manual action is simply an action that can be triggered manually using the CLI.

Many actions supports both manual and automated triggers.

How to use manual triggers
---------------------------------

Use the Robusta CLI to manually trigger a supported action:

.. code-block:: bash

    robusta playbooks trigger <action_name> name=<name> namespace=<namespace> kind=<kind> <key>=<value>

The parameters above are:

name
    The name of a Kubernetes resource

namespace
    The resource's namespace

kind
    ``pod``, ``deployment``, or any other resource the action supports. This can be left out for playbooks that support
    one input type.

<key>=<value>
    Any additional parameters the action needs
