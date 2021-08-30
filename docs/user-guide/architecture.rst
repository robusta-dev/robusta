Robusta Architecture
####################

Robusta is composed of a client-side ``robusta`` command and two in-cluster pods.

Robusta CLI
-----------

The robusta cli is installed via ``pip install robusta-cli`` and contains wrappers around kubectl to simplify
robusta operations. For example, ``robusta install`` fetches Robusta's yaml manifests, customizes them with parameters
from the user, and then runs ``kubectl apply``.

Robusta Kubernetes Deployments
------------------------------

.. image:: ../images/arch.png


All of Robusta's Kubernetes resources are installed in the ``robusta`` namespace.
You can install robusta on a custom namespace, by using the ``namespace`` parameter on the ``robusta install`` command.

Robusta has two in-cluster Kubernetes deployments which trigger and execute playbooks.
The first deployment, ``robusta-forwarder`` connects to the Kubernete's API server and monitors changes to the Kubernetes
API. All interesting changes are then forwarded to the second deployment, ``robusta-runner`` which is responsible for playbook execution.

Alternative Architectures
-------------------------
Robusta also supports agentless mode and can monitor a cluster from the outside. If you are interested in this feature please contact us.