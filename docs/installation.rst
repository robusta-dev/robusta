Install with Helm
##################

Installing Robusta takes about 90 seconds on a 10 node cluster. For test clusters, we recommend KIND. You can :ref:`upgrade or uninstall <Upgrade and Uninstall>` at any time.

This tutorial uses `Helm 3 <https://helm.sh/docs/intro/install/>`_. You can also :ref:`Install with ArgoCD`.

.. admonition:: Have questions?

    `Ask on Slack <https://join.slack.com/t/robustacommunity/shared_invite/zt-10rkepc5s-FnXKvGjrBmiTkKdrgDr~wg>`_ or open a `GitHub issue <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=other.md&title=Installation%20Question>`_

Generate a config
-----------------------------------

Robusta needs settings to work. For example, if you use Slack then Robusta needs an API key. These settings are configured as Helm values.

We'll generate the Helm values using the ``robusta`` cli tool. There are two ways to install this tool: using ``pip`` or using a Docker container with the ``robusta`` cli already inside. We recommend pip.

.. tab-set::

    .. tab-item:: pip
        :name: pip-cli-tab

        Install the ``robusta`` cli tool with ``pip``:

        .. code-block:: bash
            :name: cb-pip-install

            pip install -U robusta-cli --no-cache

        Run the ``robusta`` cli tool to generate a Helm values file:

        .. code-block:: bash
           :name: cb-robusta-gen-config

            robusta gen-config

        .. admonition:: System Requirements
            :class: warning

            Python 3.7 or higher is required.

            On systems with both Python 2 and Python 3, make sure you run ``pip3``

            You also must have Python's script directory in your PATH. When this is not the case, errors like ``command not found: robusta`` occur. See :ref:`Common Errors` to fix this.

    .. tab-item:: docker
        :name: docker-cli-tab

        Download the robusta script and grant execute permissions:

        .. code-block:: bash
            :name: cb-docker-cli-download

            curl -fsSL -o robusta https://docs.robusta.dev/master/_static/robusta
            chmod +x robusta

        Run the ``robusta`` cli tool to generate a Helm values file:

        .. code-block:: bash
            :name: cb-docker-cli-example

            ./robusta version

        .. admonition:: System Requirements
            :class: warning

            A Docker daemon and bash are required.

            On Windows you can use bash inside `WSL <https://docs.microsoft.com/en-us/windows/wsl/install>`_.

You now have a ``generated_values.yaml`` file with a Robusta config. You can customize this more later (for example, to `add integrations <https://docs.robusta.dev/master/catalog/sinks/index.html>`_ like Discord). For now, lets install Robusta and see it in action.

Run helm
------------------------------

Add Robusta's chart repository:

.. code-block:: bash
   :name: cb-helm-repo-add-update-robusta

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update

Specify your cluster's name and run ``helm install``. On some clusters this can take a while, so don't panic if it appears stuck:

.. code-block:: bash
   :name: cb-helm-install-only-robusta

    helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME> # --set isSmallCluster=true

.. admonition:: Using test clusters
    :class: important

    Test clusters like Kind and Colima tend to have fewer resources. You can lower the resource usage of Robusta by including ``--set isSmallCluster=true``. You should leave this setting out on production clusters.

    Don't install Robusta on minkube. There is a known issue.

Verify that two Robusta pods are running and there are no errors:

.. code-block:: bash
    :name: cb-get-pods-robusta-logs

    kubectl get pods -A | grep robusta
    robusta logs

See in action
------------------------------

Let's deploy a crashing pod. Robusta will identify the problem and notify us:

.. code-block:: bash
   :name: cb-apply-crashpod

   kubectl apply -f https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw

Verify that the pod is actually crashing:

.. code-block:: bash
   :name: cb-verify-crash-pod-crashing

   $ kubectl get pods -A
   NAME                            READY   STATUS             RESTARTS   AGE
   crashpod-64d8fbfd-s2dvn         0/1     CrashLoopBackOff   1          7s

Once the pod has reached two restarts, you'll get notified in the app you integrated Robusta with:

.. admonition:: Example Slack Message

    .. image:: /images/crash-report.png


Now open the `Robusta UI <https://platform.robusta.dev/>`_ (if you enabled it) and look for the same message there.

Finally, clean up the crashing pod:

.. code-block:: bash
   :name: cb-delete-crashpod

   kubectl delete deployment crashpod


Next Steps
---------------------------------

1. Learn to :ref:`track Kubernetes changes with Robusta <Automation Basics>`
2. Learn to :ref:`improve Prometheus alerts with Robusta <Alert Enrichment>`


Appendix
---------------------------------

Other installation methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. details:: Installing with GitOps

    For ArgoCD, we have a :ref:`dedicated tutorial <Install with ArgoCD>`.

    For other tools, use the instructions above to generate ``generated_values.yaml``. Commit it to git and use
    your GitOps tool to install.

.. details:: Installing without the Robusta CLI

    Using the cli is totally optional. If you prefer, you can skip the CLI and fetch the default **Helm values** from the helm chart:

    .. code-block:: bash
        :name: cb-helm-repo-add-show-values

        helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
        helm show values robusta/robusta


    Most values are documented in the :ref:`Configuration Guide`

    Do not use ``helm/robusta/values.yaml`` in the GitHub repo. It has some empty placeholders which are replaced during
    our release process.

.. details:: Installing in a different namespace

    Create a namespace ``robusta`` and install robusta in the new namespace using:

    .. code-block:: bash
        :name: cb-helm-install-robusta-custom

        helm install robusta robusta/robusta -f ./generated_values.yaml -n robusta --create-namespace

    Verify that Robusta installed two deployments in the ``robusta`` namespace:

    .. code-block:: bash
       :name: cb-get-pods-robusta-logs-custom

        kubectl get pods -n robusta

.. details:: Installing on OpenShift

    You will need to run one additional command:

    .. code-block:: bash
       :name: cb-oc-adm-policy-add

        oc adm policy add-scc-to-user anyuid -z robusta-runner-service-account

    It's possible to reduce the permissions more. Please feel free to open a PR suggesting something more minimal

