Install with Helm
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

    * Don't install Robusta on minkube. There is a known issue.
    * On test clusters like KIND and colima, we recommend including ``--set isSmallCluster=true`` because they have reduced resources. Leave this out on production clusters.


Verify that two Robusta pods are running and there are no errors:

.. code-block:: bash
    :name: cb-get-pods-robusta-logs

    kubectl get pods -A | grep robusta
    robusta logs