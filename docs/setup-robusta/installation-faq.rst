FAQ
################################

I have an error installing Robusta
================================================
Please refer to :ref:`Help <Getting Support>` for common errors and solutions.

The helm chart in GitHub doesn't work. Why?
========================================================
It has certain placeholders. For example, ``runner.image`` is set during our release workflow.

Use our Helm repository instead of our GitHub repository. See above.

Can I install Robusta in a different namespace?
================================================

Yes. By default Robusta is installed in the ``default`` namespace but you can change that.

For example, to install in the ``robusta`` namespace:

.. code-block:: bash
    :name: cb-helm-install-robusta-custom

    helm install robusta robusta/robusta -f ./generated_values.yaml -n robusta --create-namespace --set clusterName=<YOUR_CLUSTER_NAME>

Verify success by checking that Robusta pods are running:

.. code-block:: bash
   :name: cb-get-pods-robusta-logs-custom

    kubectl get pods -n robusta
