Architecture
####################

Standard Architecture
-------------------------

Robusta is composed of:

1. A client-side :ref:`robusta <CLI Commands>` cli (optional)
2. Two Kubernetes deployments, installed and managed with Helm:

Kubernetes Deployments
^^^^^^^^^^^^^^^^^^^^^^
robusta-forwarder
    Connects to the APIServer and monitors Kubernetes changes. Forwards them to robusta-runner.

robusta-runner
    Executes playbooks

.. image:: ../images/arch.png
   :width: 600
   :align: center

Alternative Architectures
-------------------------
Robusta supports agentless mode and can monitor a cluster from the outside. If you are interested in this feature please
:ref:`contact us. <Getting Support>`