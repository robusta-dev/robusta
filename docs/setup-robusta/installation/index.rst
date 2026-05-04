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

Sign Up and Install
---------------------

Sign up `for a free Robusta account ↗ <https://platform.robusta.dev/signup?utm_source=docs&utm_content=install-page>`_ and follow the install wizard. It generates a ``generated_values.yaml`` file and provides the Helm install commands tailored to your cluster.

.. note::

    **Save your generated_values.yaml file** — you'll need it to install Robusta on new clusters or upgrade. It contains sensitive values; refer to :ref:`Managing Secrets` for tips on protecting them.
