
Overview
===========

Playbooks are deterministic rules for responding to alerts and unhealthy conditions in a Kubernetes cluster.

Playbooks are recommended for advanced use cases. Most users should start with :doc:`AI Analysis </configuration/holmesgpt/main-features>` of alerts first, which requires far less configuration.

Quick Start
---------------------

New to playbooks? Start with the :doc:`Playbook Basics </playbook-reference/defining-playbooks/playbook-basics>` guide to learn how to create your first playbook.

How Playbooks Work
---------------------

Automations in Robusta are called playbooks and they are defined in YAML in your Robusta Helm values.

Every playbook consists of two parts:

* A :ref:`Trigger <Triggers Reference>` condition that defines when the automation runs
* An :ref:`Action <Actions Reference>` that defines what the automation does (typically falling into the above categories like enrich, remediate, silence, etc)

