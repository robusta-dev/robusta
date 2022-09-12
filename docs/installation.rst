Installation
##################

The standard installation uses `Helm 3 <https://helm.sh/docs/intro/install/>`_ and the robusta-cli, but :ref:`alternative methods <Additional Installation Methods>` are described below.

Configuring and installing Robusta takes 97.68 seconds on a 10 node cluster [#f1]_. You can also install on minikube or KIND. :ref:`Uninstalling <Helm Uninstall>`  takes one command, so go ahead and try!

.. admonition:: Have questions?

    `Ask us on Slack <https://join.slack.com/t/robustacommunity/shared_invite/zt-10rkepc5s-FnXKvGjrBmiTkKdrgDr~wg>`_ or open a `GitHub issue <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=other.md&title=Installation%20Question>`_

We will now configure Robusta in your cluster.
For this we need to install Robusta, and also connect at least one destination ("sink"), and at least one source ("triggers").

.. image:: ./images/robusta_motion_graphics_transparent.gif
   :align: center

Creating the config file
------------------------------

1.  To configure robusta, the Robusta CLI is required. Choose one of the installation methods below.

.. admonition:: Installation Methods

    .. tab-set::

        .. tab-item:: PIP
            :name: pip-cli-tab

            .. code-block:: bash
                :name: cb-pip-install

                pip install -U robusta-cli --no-cache

            .. admonition:: Common Errors
                :class: warning

                * Python 3.7 or higher is required
                * If you are using a system such as macOS that includes both Python 2 and Python 3, run pip3 instead of pip.
                * Errors about *tiller* mean you are running Helm 2, not Helm 3

        .. tab-item:: Docker
            :name: docker-cli-tab

            For **Windows** please use `WSL <https://docs.microsoft.com/en-us/windows/wsl/install>`_.

            * Download robusta script and give it executable permissions:

            .. code-block:: bash
                :name: cb-docker-cli-download

                curl -fsSL -o robusta https://docs.robusta.dev/master/_static/robusta
                chmod +x robusta

            * Use the script, for example:

            .. code-block:: bash
                :name: cb-docker-cli-example

                ./robusta version

            .. admonition:: Common Errors
                :class: warning

                * Docker daemon is required.

2. Generate a Robusta configuration. This will setup Slack and other integrations. We **highly recommend** enabling the cloud UI so you can see all features in action.

.. code-block:: bash
   :name: cb-robusta-gen-config

    robusta gen-config

.. admonition:: Robusta on Minikube
    :class: warning

    We don't recommend installing Robusta on Minikube because of a recent issue with minikube. More details `here <https://github.com/kubernetes/minikube/issues/14806>`_. 

.. admonition:: Robusta not in PATH
    :class: warning

    if you get "``command not found: robusta``", see :ref:`Common errors <Common Errors>`

3. Save ``generated_values.yaml``, somewhere safe. This is your Helm ``values.yaml`` file.

.. admonition:: Installing on multiple clusters
    :class: important

    Use the same ``generated_values.yaml`` for all your clusters (dev, prod, etc..). There's no need to run gen-config again.

Standard Installation
------------------------------

1. Add Robusta's chart repository:

.. code-block:: bash
   :name: cb-helm-repo-add-update-robusta

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update

2. Copy the cluster name from the current context and install Robusta using Helm. On some clusters this can take a while [#f2]_, so don't panic if it appears stuck:

.. admonition:: Test clusters (e.g Kind, MiniKube, Colima)
    :class: important

    Test clusters tend to have fewer resources. To lower the resource requests of Robusta,
    include ``--set isSmallCluster=true`` at the end of the install command.

.. code-block:: bash
   :name: cb-helm-install-only-robusta

    helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME> # --set isSmallCluster=true

3. Verify the two Robusta pods and running with no errors in the logs:

.. code-block:: bash
    :name: cb-get-pods-robusta-logs

    kubectl get pods -A | grep robusta
    robusta logs

Seeing Robusta in action
------------------------------

By default, Robusta sends notifications when Kubernetes pods crash.

1. Create a crashing pod:

.. code-block:: bash
   :name: cb-apply-crashpod

   kubectl apply -f https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw

2. Verify that the pod is actually crashing:

.. code-block:: bash
   :name: cb-verify-crash-pod-crashing

   $ kubectl get pods -A
   NAME                            READY   STATUS             RESTARTS   AGE
   crashpod-64d8fbfd-s2dvn         0/1     CrashLoopBackOff   1          7s

3. Once the pod has reached two restarts, check your Slack channel for a message about the crashing pod.

.. admonition:: Example Slack Message

    .. image:: /images/crash-report.png


4. Open the `Robusta UI <https://platform.robusta.dev/>`_ (if you enabled it) and look for the same message there.

5. Clean up the crashing pod:

.. code-block:: bash
   :name: cb-delete-crashpod

   kubectl delete deployment crashpod

Installing a second cluster
---------------------------------

When installing a second cluster on the same account, there's no need to run ``robusta gen-config`` again.

Using your existing generated_values.yaml and the new clusterName run:

.. code-block:: bash
   :name: cb-helm-install-only-robusta

    helm install robusta robusta/robusta -f ./generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME> # --set isSmallCluster=true

.. admonition:: Where is my generated_values.yaml?

    If you have lost your ``generated_values.yaml`` file, you can extract it from any cluster running Robusta.


    In that case, ``clusterName`` and ``isSmallCluster`` may be already in ``generated_values.yaml``. Make sure to remove them before installing on the new cluster.

    .. code-block:: bash

         helm get values -o yaml robusta | grep -v clusterName: | grep -v isSmallCluster: > generated_values.yaml


Next Steps
---------------------------------

1. Define your :ref:`first automation <Automation Basics>`
2. Add your first :ref:`Prometheus enrichment <Alert Enrichment>`

.. rubric:: Footnotes

.. [#f1] `See this great video on YouTube where a community member installs Robusta with a stopwatch. <https://www.youtube.com/watch?v=l_zaCaY_wls>`_ If you beat his time by more than 30% and document it, we'll send you a Robusta mug too.

.. [#f2] AWS EKS, we're looking at you!


Additional Installation Methods
---------------------------------

.. dropdown:: Installing with GitOps
    :color: light

    Follow the instructions above to generate ``generated_values.yaml``. Commit it to git and use ArgoCD or
    your favorite tool to install.

.. dropdown:: Installing without the Robusta CLI
    :color: light

    Using the cli is totally optional. If you prefer, you can skip the CLI and fetch the default ``values.yaml``:

    .. code-block:: bash
        :name: cb-helm-repo-add-show-values

        helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
        helm show values robusta/robusta


    Most values are documented in the :ref:`Configuration Guide`

    Do not use the ``values.yaml`` file in the GitHub repo. It has some empty placeholders which are replaced during
    our release process.

.. dropdown:: Installing in a different namespace
    :color: light

    Create a namespace ``robusta`` and install robusta in the new namespace using:

    .. code-block:: bash
        :name: cb-helm-install-robusta-custom

        helm install robusta robusta/robusta -f ./generated_values.yaml -n robusta --create-namespace

    Verify that Robusta installed two deployments in the ``robusta`` namespace:

    .. code-block:: bash
       :name: cb-get-pods-robusta-logs-custom

        kubectl get pods -n robusta

.. dropdown:: Installing on OpenShift
    :color: light

    You will need to run one additional command:

    .. code-block:: bash
       :name: cb-oc-adm-policy-add

        oc adm policy add-scc-to-user anyuid -z robusta-runner-service-account

    It's possible to reduce the permissions more. Please feel free to open a PR suggesting something more minimal

