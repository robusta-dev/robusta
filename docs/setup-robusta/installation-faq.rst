FAQ
################################

I have an error installing Robusta
================================================
Please refer to :ref:`Help <Getting Support>` for common errors and solutions.

Can I install Robusta without the cli?
========================================
Yes, using the cli is optional. It auto-generates helm values, but you can also handwrite them:

1. Fetch Robusta's default **Helm values**:

.. code-block:: bash
    :name: cb-helm-repo-add-show-values

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
    helm show values robusta/robusta

2. Modify those values to your heart's content. Refer to the :ref:`Integration Guide <Integrations Overview>` for details.

3. Do a ``helm install``.

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

.. warning::

    Make sure you add the ``--namespace`` flag to future ``robusta`` cli commands.

Does Robusta support Thanos/Cortex/Mimir/VictoriaMetrics?
============================================================
Any Prometheus-compatible solution is fine. Just follow instructions under :ref:`Integrate with Existing Prometheus`

Can I use Robusta with DataDog?
============================================================
Yes, we have a :ref:`DataDog integration <DataDog>` available. Try it out.

Is NewRelic supported?
=======================
It's being planned, speak to us on Slack.

Does Robusta replace monitoring tools?
============================================================
Robusta's :ref:`all-in-one package <Install Robusta + Prometheus>` is a complete monitoring and observability solution.

Alternatively, you can keep your existing tools and add-on robusta.
