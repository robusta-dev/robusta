:hide-toc:

.. _Getting Support:

Getting Support
================

.. toctree::
   :maxdepth: 1
   :hidden:


Ask for help, or just say hi!

.. grid:: 5
   :gutter: 3

   .. grid-item-card:: :octicon:`comment-discussion;1em;` Slack
      :class-card: sd-bg-light sd-bg-text-light
      :link: https://bit.ly/robusta-slack


   .. grid-item-card:: :octicon:`mark-github;1em;` Github Issue
      :class-card: sd-bg-light sd-bg-text-light
      :link: https://github.com/robusta-dev/holmesgpt/issues

--------------------------------
Commercial Support
--------------------------------
Contact support@robusta.dev for details.

--------------------------------
Troubleshooting Guide
--------------------------------

Issues are organized by installation phase to help you quickly find solutions.

**Quick Diagnosis:**

.. raw:: html

   <div style="margin: 20px 0; padding: 15px; background-color: #f0f7ff; border-left: 4px solid #0066cc;">
   <strong>Where are you stuck?</strong><br>
   • <a href="#phase-1-helm-installation">Phase 1: Helm Installation</a> - Helm install/upgrade failures<br>
   • <a href="#phase-2-runtime-issues">Phase 2: Runtime Issues</a> - Alerts not arriving, pods crashing<br>
   • <a href="#phase-3-integration-issues">Phase 3: Integration Issues</a> - Slack, Prometheus connection problems
   </div>

Phase 1: Helm Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^

Problems when running ``helm install`` command or installing via GitOps.

.. details:: unknown field in com.coreos.monitoring.v1.Prometheus.spec, ValidationError(Prometheus.spec)

    This indicates potential discrepancies between the version of Prometheus you are trying to use and the version of the CRDs in your cluster.

    Follow this guide for :ref:`upgrading CRDs from an older version <Manual Upgrade>`.

.. details:: at least one sink must be defined

   Verify ``sinksConfig`` is defined in your Robusta values file, with at least one sink like Slack or Teams. If it's your first time installing, the fastest solution is to start configue creation from scratch.

   .. code-block:: bash

      Error: UPGRADE FAILED: execution error at (robusta/templates/playbooks-config.yaml:9:7): At least one sink must be defined!

.. details:: CustomResourceDefinition.apiextensions.k8s.io "prometheuses.monitoring.coreos.com" is invalid: metadata.annotations: Too long

      This is often a CRD issue which can be fixed by enabling server-side apply option as shown below. Check out `this blog <https://blog.ediri.io/kube-prometheus-stack-and-argocd-25-server-side-apply-to-the-rescue>`_ to learn more. 

      .. image:: /images/Argocd_crd_issue_fix.png 
        :width: 400
        :align: center

.. details:: one or more objects failed to apply... CustomResourceDefinition.apiextensions.k8s.io "prometheusagents.monitoring.coreos.com" is invalid

      This indicates potential discrepancies between the version of Prometheus you are trying to use and the version of the CRDs in your cluster.

      Follow this guide for :ref:`upgrading CRDs from an older version <Manual Upgrade>`.

.. details:: CustomResourceDefinition.apiextensions.k8s.io "prometheuses.monitoring.coreos.com" is invalid


      This indicates potential discrepancies between the version of Prometheus you are trying to use and the version of the CRDs in your cluster.

      Follow this guide for :ref:`upgrading CRDs from an older version <Manual Upgrade>`.

Phase 2: Runtime Issues
^^^^^^^^^^^^^^^^^^^^^^^

Issues after installation when pods are running but not working correctly.

**robusta-runner pod issues**

.. details:: robusta-runner pod is in Pending state due to memory issues

    If your cluster has 20 Nodes or less, set robusta-runner's memory request to 512MiB in Robusta's Helm values:

    .. code-block:: yaml

        runner:
          resources:
            requests:
              memory: 512MiB
            limits:
              memory: 512MiB

.. details:: robusta-runner isn't working or has exceptions

        Start by checking the logs for errors:

        .. code-block:: bash

                kubectl get pods -A | grep robusta-runner # get the name and the namespace of the robusta pod
                kubectl logs -n <NAMESPACE> <ROBUSTA-RUNNER-POD-NAME> # get the logs


        .. details:: Blocked by firewall / HTTP proxy

                If your Kubernetes cluster is behind an HTTP proxy or firewall, follow the instructions in :ref:`Deploying Behind Proxies` to ensure Robusta has the necessary access.

**Prometheus issues**

.. details:: Prometheus' pods are in Pending state due to memory issues

        If your cluster has 20 Nodes or less, set Prometheus memory request to 1Gi in Robusta's Helm values:

        .. code-block:: yaml

                kube-prometheus-stack:
                  prometheus:
                    prometheusSpec:
                      resources:
                        requests:
                          memory: 1Gi
                        limits:
                          memory: 1Gi

        If using a test cluster like Kind/Colima, re-install Robusta with the ``isSmallCluster=true`` property.
        If you're also using Robusta's kube-prometheus-stack, add the lines involving prometheusSpec.

        .. code-block:: bash

                helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME> --set isSmallCluster=true \
                    --set kube-prometheus-stack.prometheus.prometheusSpec.retentionSize=9GB \
                    --set kube-prometheus-stack.prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi \
                    --set kube-prometheus-stack.prometheus.prometheusSpec.resources.requests.memory=512Mi


Phase 3: Integration Issues
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Problems with external service integrations after Robusta is running.

**Slack Integration**

.. details:: Slack notifications not arriving

    1. Verify Slack webhook URL is correct in your values.yaml
    2. Check robusta-runner logs for Slack-related errors:

    .. code-block:: bash

        kubectl logs -n <NAMESPACE> <ROBUSTA-RUNNER-POD-NAME> | grep -i slack

    3. Test the webhook URL manually using curl
    4. Ensure the Slack app has proper permissions in your workspace

**Prometheus Connection Issues**

.. details:: Cannot connect to Prometheus

    1. Verify Prometheus URL in your configuration
    2. Check if Prometheus is accessible from robusta-runner pod:

    .. code-block:: bash

        kubectl exec -n <NAMESPACE> <ROBUSTA-RUNNER-POD-NAME> -- wget -qO- <PROMETHEUS_URL>/api/v1/status/config

    3. For managed Prometheus services, verify authentication tokens and endpoints

**Teams/Email Integration**

.. details:: Microsoft Teams or email notifications not working

    1. Verify webhook URLs and authentication credentials
    2. Check for network connectivity issues
    3. Review logs for integration-specific error messages

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Alert Manager is not working
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. details:: Not getting alert manager alerts

        Receiver url has namespace TBD




.. details:: AlertManager Silences are Disappearing

        This happens when AlertManager does not have persistent storage enabled.

        When using Robusta's embedded Prometheus Stack, persistent storage is enabled by default.

        For other Prometheus distributions set the following Helm value (or it's equivalent):

        .. code-block::

                  # this is the setting in in kube-prometheus-stack
                  # the exact setting will differ for other Prometheus distributions
                  alertmanager:
                    alertmanagerSpec:
                      storage:
                        volumeClaimTemplate:
                          spec:
                            accessModes: ["ReadWriteOnce"]
                            resources:
                              requests:
                                storage: 10Gi

