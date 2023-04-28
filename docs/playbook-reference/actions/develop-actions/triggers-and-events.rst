Events and Triggers
=====================

When configuring Robusta as a user, you define :ref:`triggers <Triggers>` in ``generated_values.yaml`` but when writing playbook
actions you deal with events.

The basic idea is that **triggers** generate **event** objects and those events are passed to **action** functions.

Lifecycle of a Robusta Event
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. A pod changes
2. The API Server notifies Robusta
3. Robusta checks if any triggers like ``on_pod_update`` are activated by the pod change
4. If yes, Robusta calls that trigger
5. The trigger converts data from the APIServer to a concrete event like ``PodEvent``
6. The ``PodEvent`` is passed to all playbook actions

Compatibility of Actions and Events
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This is discussed in :ref:`Trigger-Action Compatibility` from the perspective of a user who configures playbooks in YAML.

Let's look at this from the perspective of a developer who is writing a playbook action in Python.

You declare which events your playbook is compatible with by choosing the first parameter of your playbook's Python function. For example:

.. code-block:: python

    @action
    def delete_pod(event: PrometheusKubernetesAlert):
    if not event.get_pod():
        logging.info("alert is not related to pod")
        return

    event.get_pod().delete()

The above action takes ``PrometheusKubernetesAlert`` as input and can therefore only be connected to an ``on_prometheus_alert`` trigger as no other trigger generates that event object.

However, this action doesn't actually need a Prometheus alert as input as it does nothing with the alert itself. We can modify this action so it takes a ``PodEvent`` as input.

.. code-block:: python

    @action
    def delete_pod(event: PodEvent):
    if not event.get_pod():
        logging.info("alert is not related to pod")
        return

    event.get_pod().delete()

``PrometheusKubernetesAlert`` is a subclass of ``PodEvent``, so general object-oriented principles apply here:
``PrometheusKubernetesAlert`` can be used wherever ``PodEvent`` is expected.

Therefore this action can be triggered with ``on_prometheus_alert`` but it can **also** be triggered on any other PodEvent.

Which Triggers are Compatible with Which Events?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Here is the Robusta event hierarchy:

.. image:: /images/Event_Hierarchy/Event_Hierarchy_Diagram.drawio.svg
    :align: center

..
    this is a sphinx comment
    the above image was generated like this by a patched version of inheritance-diagram based on
    https://github.com/sphinx-doc/sphinx/pull/8159
    .. inheritance-diagram2:: robusta.api.ExecutionBaseEvent
        :parts: 1
        :include-subclasses:

.. note::

    Note that ``PrometheusKubernetesAlert`` inherits from many Kubernetes event classes, so you can use
    ``on_prometheus_alert`` with many types of playbook actions. For example, ``on_prometheus_alert`` is
    compatible with any playbook that accepts ``PodEvent``, ``NodeEvent``, ``DeploymentEvent``, and so on.
    However, at runtime the alert must contain a relevant label in order to map the alert to the relevant
    Kubernetes object.

Writing Actions that Support Manual Triggers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You're writing a playbook action and you'd like to support :ref:`manual triggers`. It's easy.

All classes above with names like ``PodEvent`` support manual triggers automatically. When running the manual trigger
specify the pod's name and Robusta will generate an artificial event.

On the other hand, events like ``PodChangeEvent`` don't support manual triggers. ``PodChangeEvent`` cannot be generated
artificially because it requires two versions of the pod - a before and after version.

