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
