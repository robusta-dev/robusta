More installation methods
################################

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

