Robusta Architecture
####################

Robusta is composed of a client-side ``robusta`` command and two in-cluster pods.

Client-side components
---------------------------

The robusta cli is installed via ``pip install robusta-cli`` and contains utilities to simplify robusta operations.
For example, ``robusta playbooks trigger`` allows manually triggering playbooks.

Kubernetes components
------------------------------

.. image:: ../images/arch.png
   :width: 600
   :align: center

All of Robusta's Kubernetes resources are installed and managed with Helm.

Robusta installs two Kubernetes deployments. The first deployment, ``robusta-forwarder`` connects to the
Kubernetes API server and monitors changes to Kubernetes resources. Interesting changes are then forwarded to the
second deployment, ``robusta-runner``, which is responsible for playbook execution.

Alternative Architectures
-------------------------
Robusta supports agentless mode and can monitor a cluster from the outside. If you are interested in this feature please contact us.