Installation
##################

The standard installation uses `Helm 3 <https://helm.sh/docs/intro/install/>`_ and the robusta-cli, but :ref:`alternative methods <Additional Installation Methods>` are described below. 

Configuring and installing Robusta takes 97.68 seconds on a 10 node cluster [#f1]_. You can also install on minikube or KIND. :ref:`Uninstalling <Helm Uninstall>`  takes one command, so go ahead and try!

Standard Installation
------------------------------

1. Download the Helm chart and install Robusta-CLI:

.. code-block:: bash

   helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
   pip install -U robusta-cli --no-cache
   

.. admonition:: Common Errors
    :class: warning

    * If you are using a system such as macOS that includes both Python 2 and Python 3, run pip3 instead of pip.
    * Errors about *tiller* mean you are running Helm 2, not Helm 3

2. Generate a Robusta configuration. This will setup Slack and other integrations. We **highly recommend** enabling the cloud UI so you can see all features in action.

.. code-block:: bash

    robusta gen-config

3. Save ``generated_values.yaml``, somewhere safe. This is your Helm ``values.yaml`` file.

4. Install Robusta using Helm. On some clusters this can take a while [#f2]_, so don't panic if it appears stuck:

.. code-block:: bash

    helm install robusta robusta/robusta -f ./generated_values.yaml

5. Verify that Robusta is running two pods and there are no errors in the logs:

.. code-block:: bash

    kubectl get pods
    robusta logs

Seeing Robusta in action
------------------------------

By default, Robusta sends Slack notifications when Kubernetes pods crash.

1. Create a crashing pod:

.. code-block:: bash

   kubectl apply -f https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw


2. Verify that the pod is actually crashing:

.. code-block:: bash

   $ kubectl get pods -A
   NAME                            READY   STATUS             RESTARTS   AGE
   crashpod-64d8fbfd-s2dvn         0/1     CrashLoopBackOff   1          7s

3. Once the pod has reached two restarts, check your Slack channel for a message about the crashing pod.

.. admonition:: Example Slack Message

    .. image:: /images/crash-report.png


4. Clean up the crashing pod:

.. code-block:: bash

   kubectl delete deployment crashpod

Forwarding Prometheus Alerts to Robusta
----------------------------------------

Robusta can suggest fixes for your existing Prometheus alerts and tell you why they happen.

First, you must configure an :ref:`AlertManager webhook. <Sending Alerts to Robusta>`

If you installed Robusta's bundled Prometheus Stack then you can skip this step.

Next Steps
---------------------------------

1. Define your first automation to :ref:`track Kubernetes changes <Track Kubernetes Changes>`
2. Add your first :ref:`Prometheus enrichment <Improve Prometheus Alerts>`
3. Complete the :ref:`manual troubleshooting tutorial <Python Profiling>`
4. Explore the Robusta UI (use the URL you received during installation)

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

        helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
        helm show values robusta/robusta


    Most values are documented in the :ref:`Configuration Guide`

    Do not use the ``values.yaml`` file in the GitHub repo. It has some empty placeholders which are replaced during
    our release process.

.. dropdown:: Installing in a different namespace
    :color: light

    Create a namespace ``robusta`` and install robusta in the new namespace using:

    .. code-block:: bash

        helm install robusta robusta/robusta -f ./generated_values.yaml -n robusta --create-namespace

    Verify that Robusta installed two deployments in the ``robusta`` namespace:

    .. code-block:: bash

        kubectl get pods -n robusta

.. dropdown:: Installing on OpenShift
    :color: light
    
    You will need to run one additional command:

    .. code-block:: bash

        oc adm policy add-scc-to-user anyuid -z robusta-runner-service-account

    It's possible to reduce the permissions more. Please feel free to open a PR suggesting something more minimal

.. dropdown:: Installing a second cluster
    :color: light

    When installing a second cluster on the same account, there is no need to run ``robusta gen-config`` again.

    Just change ``clusterName`` in values.yaml. It can have any value as long as it is unique between clusters.

