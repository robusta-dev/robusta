Robusta UI
#################

The Robusta UI sink connects your Robusta installation to the Robusta SaaS platform, where you can investigate alerts with HolmesGPT, review timelines, and more.

For the full list of platform features, see `home.robusta.dev <https://home.robusta.dev>`_.


Configuring the Robusta UI Sink
------------------------------------------------

.. tip::
    This guide is for users who have already installed Robusta on their cluster. If you haven't installed Robusta yet, we recommend starting by :robusta-url:`creating a free Robusta UI account ↗ <https://platform.robusta.dev/signup?utm_source=docs&utm_content=robusta-ui-sink-page>` instead.

Use the ``robusta`` CLI to generate a token:

.. code-block::
   :name: cb-robusta-ui-sink-generate-token

    robusta integrations ui

Add a new sink to your Helm values (``generated_values.yaml``), under ``sinksConfig``, with the token you generated:

.. code-block:: bash
  :name: cb-robusta-ui-sink-config-basic

  sinksConfig:
  - robusta_sink:
      name: robusta_ui_sink
      token: <your-token>
      ttl_hours: 4380

Perform a :ref:`Helm Upgrade <Simple Upgrade>`.

Handling Short-Lived Clusters in the UI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

   This is a Robusta classic feature for Kubernetes monitoring and does not apply to HolmesGPT.

By default, inactive Robusta clusters will be kept in the UI for 6 months **data retention**. (4380 hours)

If you have many short-lived clusters, you can remove them from the UI automatically once they stop running.
To do so, configure a shorter retention period by setting the ``ttl_hours`` in the Robusta UI sink settings:

.. code-block:: bash
  :name: cb-robusta-ui-sink-config-ttl

  sinksConfig:
  - robusta_sink:
      name: robusta_ui_sink
      token: <your-token>
      # automatically clean up old clusters in the UI if they are disconnected 12+ hours
      ttl_hours: 12


.. _cb-robusta-ui-sink-namespace-config:

Monitoring Specific Resources in Namespaces
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

   This is a Robusta classic feature for Kubernetes monitoring and does not apply to HolmesGPT.

By default, the Robusta UI sink discovers the standard resources in all namespaces using the standard discovery interval.
However, we have a configuration to monitor custom namespaced resources, and an API is exposed via the Robusta Backend to see how many of each resource you have in a namespace.

To configure this, use the ``namespace_discovery_seconds`` and ``namespaceMonitoredResources`` settings in the Robusta UI sink:

.. code-block:: bash
  :name: cb-robusta-ui-sink-namespace-config-code

  sinksConfig:
  - robusta_sink:
      name: robusta_ui_sink
      token: <your-token>
      # how often to re-scan for new namespaces (in seconds)
      namespace_discovery_seconds: 3600
      # what resource types to actively count per namespace
      namespaceMonitoredResources:
        - apiGroup: ""
          apiVersion: "v1"
          kind: "Services"
        - apiGroup: "apps"
          apiVersion: "v1"
          kind: "Deployments"
        - apiGroup: "apps.openshift.io"
          apiVersion: "v1"
          kind: "DeploymentConfig"
        - apiGroup: "batch"
          apiVersion: "v1"
          kind: "CronJob"
        - apiGroup: "networking.k8s.io"
          apiVersion: "v1"
          kind: "Ingress"



More Information about the UI
-------------------------------------
For more information on UI features, view `robusta.dev <https://home.robusta.dev>`_.
