:hide-footer:

:tocdepth: 2

.. _install:
.. _install-barebones:

Install Robusta
================

Use Robusta's AI Agent alongside any observability stack — DataDog, NewRelic, Prometheus, SolarWinds, and more.

Prerequisites
---------------------

* A :ref:`supported Kubernetes cluster <Supported Clusters>`
* Helm

Generate a Config
-----------------------------------

Robusta needs settings to work. For example, if you use Slack then Robusta needs a Slack API key. These settings are configured as Helm values.

Sign up `for a free Robusta account ↗ <https://platform.robusta.dev/signup?utm_source=docs&utm_content=install-page>`_ to generate the configuration. The signup wizard produces a ``generated_values.yaml`` file you'll use with Helm.

**Save this file!** You'll need it to install Robusta on new clusters. It contains sensitive values — refer to :ref:`Managing Secrets` for tips on protecting them.

.. include:: ./_helm_install_no_prometheus.inc.rst


Next Steps
---------------------------------

1. :doc:`Send alerts to Robusta </configuration/index>`
2. :doc:`Investigate your alerts with AI </configuration/holmesgpt/main-features>`
