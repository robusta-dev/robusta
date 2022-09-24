Architecture
####################

Standard Architecture
-------------------------

Robusta is installed and managed with Helm.

Automations engine
^^^^^^^^^^^^^^^^^^^^^^
The main component of Robusta is the automation engine, which runs in-cluster as two Kubernetes deployments

robusta-forwarder
    Connects to the APIServer and monitors Kubernetes changes. Forwards them to robusta-runner.

robusta-runner
    Executes playbooks

.. image:: ./images/arch-1/arch-1.png
   :width: 600
   :align: center

Bundled Prometheus stack (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Robusta includes an optional :ref:`embedded Prometheus stack`, preconfigured with alerts for Kubernetes according to best practices.

If you already use *kube-prometheus-stack*, you can :ref:`point it at Robusta<Sending Alerts to Robusta>` instead.

Web UI (optional)
^^^^^^^^^^^^^^^^^^^^^^
There is a `web UI <http://home.robusta.dev/ui?from=docs>`_ [#f1]_ which provides a single pane of glass to monitor
all your alerts and pods across multiple clusters.

CLI (optional)
^^^^^^^^^^^^^^^^
The :ref:`robusta cli <CLI Commands>` has two main uses:

1. Making it easier to install Robusta by autogenerating Helm values
2. Manually triggering Robusta troubleshooting workflows (e.g. to grab a heap dump from any Java pod)

It also has features useful for developing Robusta itself.

See also
^^^^^^^^^

* `Comparison of Robusta and a bare-bones Prometheus stack without Robusta <https://home.robusta.dev/prometheus-based-monitoring/?from=docs>`_

.. rubric:: Footnotes

.. [#f1] This is the only component that isn't open source and it's completely optional. :ref:`It can be self-hosted. <Self hosted architecture>`
