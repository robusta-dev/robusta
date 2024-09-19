.. _openshift-permissions:

OpenShift
========================================

Robusta supports OpenShift. To use Robusta on OpenShift, update your Helm values (``generated_values.yaml``) as follows:

.. code-block:: yaml

    openshift:
      enabled: true
      createScc: true

    globalConfig:
      prometheus_url: https://<PROM_HOST> # get the value for <PROM_HOST> by running    oc get routes -n openshift-monitoring prometheus-k8s -o jsonpath='{.spec.host}'
      alertmanager_url: https://<AM_HOST> # get the value for <AM_HOST> by running      oc get routes -n openshift-monitoring alertmanager-main -o jsonpath='{.spec.host}'

.. warning::

      Do **not** install Robusta in the ``default`` OpenShift project.

Installing Robusta without full admin permissions
-------------------------------------------------------

If you are installing Robusta via a user that doesn't have full admin permissions on the cluster, you can
ask an admin to create the Robusta SCC for you in advance, so that you can reference it in your Helm values.

First create an SCC based on
`openshift-scc-baseline.yaml <https://github.com/robusta-dev/robusta/blob/master/helm/robusta/templates/openshift-scc-baseline.yaml>`_ file for the baseline SCC for the product. This SCC can be
and then update your Helm values with:

.. code-block:: yaml

    openshift:
      enabled: true
      createScc: false
      sccName: my-admins-scc # reference the existing SCC your admin created

A test installation in OpenShift can use the existing SCC ``anyuid``.

Optional: Giving Robusta extra debug permissions
---------------------------------------------------------

Some lesser used Robusta features require more permissions than the baseline SCC provides.

In order to support the ``python_debugger``, ``java_debugger`` and ``node_disk_analyzer``
playbooks, permission to run a far more privileged container needs to be granted to
the ``runner`` service account. This container has ``SYS_ADMIN`` capabilities and must
run as root on the node.

To support these features in a production environment, you may want to only temporarily
enable this permission so that a normal request cannot bypass the the less permissive SCC found
in the baseline. To enable these privileged operations in your OpenShift environment,
update the ``generated_values.yaml`` as follows:

.. code-block:: yaml

    openshift:
      enabled: true
      createScc: true
      createPrivilegedScc: true

You may also reference an existing SCC using the ``openshift.privilegedSccName`` value.
In test environments, you can reference the ``privileged`` SCC to enable these features in your
installation.
