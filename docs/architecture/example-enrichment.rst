:hide-toc:

Overview
================================

.. grid:: 6 6

    .. grid-item::

        Robusta is an automation and observability engine for Kubernetes. Robusta listens to Prometheus alerts,
        Kubernetes events, and more. Using a set of YAML rules, it correlates those events and acts upon them.

        It then forwards the same events (or derived events) with added context to destinations like Slack, MSTeams, and more.

        The end result is better alerts, with more relevant data, and less noise.


    .. grid-item::

        .. image:: /images/architecture-overview.png
           :width: 700px
           :align: center

Lets take a concrete ex