:hide-toc:

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
      :link: https://github.com/robusta-dev/robusta/issues

--------------------------------
Commercial Support
--------------------------------
Contact support@robusta.dev for details.

--------------------------------
Common Errors
--------------------------------

This list contains some common errors we have encountered over time.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Robusta CLI tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Errors installing the robusta cli config creation tool. Not relevant when using the Web Installation method.

.. details:: command not found: robusta (CLI not in path)

    1. Determine where the Robusta-cli binary file is located

    .. code-block:: bash
        :name: cb-find-python-cli-loc

        find / -regex '.*/bin/robusta' 2>/dev/null

    2. Add the path you found (e.g ``/opt/homebrew/bin/``) to your PATH. To do so, find your shell config file ( ~/.profile or ~/.bash_profile or ~/.zshrc etc...) and append the following:

    .. code-block:: bash
        :name: add-path-var

        export PATH="$PATH:<new-path>"

    3. Reopen the terminal or run:

    .. code-block:: bash
        :name: cb-refresh-terminal

        source <your-shell-config-file>

    .. admonition:: Alternative Solution

      Instead of modifying PATH, run Robusta commands via the python3 binary: ``python3 -m robusta.cli.main gen-config``

.. details:: SSL certificate errors on Mac OS

    This implies a python package with certificates is missing on your system.

    To fix it, run ``/Applications/Python 3.9/Install Certificates.command``

    For more info see:
    https://stackoverflow.com/questions/52805115/certificate-verify-failed-unable-to-get-local-issuer-certificate

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Helm installation fails
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Problems when running ``helm install`` command or installing via GitOps.

.. details:: unknown field in com.coreos.monitoring.v1.Prometheus.spec, ValidationError(Prometheus.spec)

    This indicates potential discrepancies between the version of Prometheus you are trying to use and the version of the CRDs in your cluster.

    Follow this guide for :ref:`upgrading CRDs from an older version <Manual Upgrade>`.

.. details:: at least one sink must be defined

   Verify ``sinksConfig`` is defined in your Robusta values file, with at least one sink like Slack, Teams or Robusta UI ("robusta_sink"). If it's your first time installing, the fastest solution is to start configue creation from scratch.

   .. code-block:: bash

      Error: UPGRADE FAILED: execution error at (robusta/templates/playbooks-config.yaml:9:7): At least one sink must be defined!

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Robusta runner, Prometheus or Holmes failures
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

robusta-runner
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

        .. details:: Discovery Error

                .. code-block::

                    2023-04-17 23:37:43.019 ERROR    Discovery process internal error
                    2023-04-17 23:37:43.022 INFO     Initialized new discovery pool
                    2023-04-17 23:37:43.022 ERROR    Failed to run publish discovery for robusta_ui_sink
                    Traceback (most recent call last):
                      File "/app/src/robusta/core/sinks/robusta/robusta_sink.py", line 175, in __discover_resources
                        results: DiscoveryResults = Discovery.discover_resources()
                      File "/app/src/robusta/core/discovery/discovery.py", line 288, in discover_resources
                        raise e
                      File "/app/src/robusta/core/discovery/discovery.py", line 280, in discover_resources
                        return future.result()
                      File "/usr/local/lib/python3.9/concurrent/futures/_base.py", line 446, in result
                        return self.__get_result()
                      File "/usr/local/lib/python3.9/concurrent/futures/_base.py", line 391, in __get_result
                        raise self._exception
                    concurrent.futures.process.BrokenProcessPool: A process in the process pool was terminated abruptly while the future was running or pending.

                This error might be due to memory issues. Increase the memory request in Robusta's Helm values:

                .. code-block:: yaml

                        runner:
                          resources:
                            requests:
                              memory: 2048Mi
                            limits:
                              memory: 2048Mi

        .. details:: Blocked by firewall / HTTP proxy

                If your Kubernetes cluster is behind an HTTP proxy or firewall, follow the instructions in :ref:`Deploying Behind Proxies` to ensure Robusta has the necessary access.


Prometheus
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Holmes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. details:: Error in Holmes: binascii.a2b_base64(s, strict_mode=validate)

        If the Holmes pod fail to start, with this exception:

        .. code-block::

                2024-09-20 15:37:57.961 INFO     loading config /etc/robusta/config/active_playbooks.yaml
                Traceback (most recent call last):
                  File "/app/server.py", line 65, in <module>
                    dal = SupabaseDal()
                          ^^^^^^^^^^^^^
                  File "/app/holmes/core/supabase_dal.py", line 38, in __init__
                    self.enabled = self.__init_config()
                                   ^^^^^^^^^^^^^^^^^^^^
                  File "/app/holmes/core/supabase_dal.py", line 68, in __init_config
                    robusta_token = self.__load_robusta_config()
                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                  File "/app/holmes/core/supabase_dal.py", line 61, in __load_robusta_config
                    return RobustaToken(**json.loads(base64.b64decode(token)))
                                                     ^^^^^^^^^^^^^^^^^^^^^^^
                  File "/usr/local/lib/python3.11/base64.py", line 88, in b64decode
                    return binascii.a2b_base64(s, strict_mode=validate)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                binascii.Error: Invalid base64-encoded string: number of data characters (21) cannot be 1 more than a multiple of 4


        It's often because the ``Robusta UI Token`` is pulled from a secret, and Holmes cannot read it.

        See :ref:`Reading the Robusta UI Token from a secret in HolmesGPT` to configure Holmes to read the ``token``

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Alert Manager is not working
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. details:: Not getting alert manager alerts

        Receiver url has namespace TBD

        .. tip::

            If you're using the Robusta UI, you can test alert routing by `Simulating an alert <https://platform.robusta.dev/simulate-alert/>`_.



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


CRD issues
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

