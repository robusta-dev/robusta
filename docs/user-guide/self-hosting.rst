Self hosting
################################

There are several ways to use Robusta:

- :ref:`Robusta Open Source (OSS)<Installation>`: Install Robusta open source project to monitor your cluster.
- Robusta OSS + Cloud `Robusta UI <https://home.robusta.dev/ui/>`_: Robusta OSS combined with a powerful UI. No need to install the UI.
- Robusta OSS + Self hosted Robusta UI: Manage the UI yourself, installed on a your own Kubernetes cluster.

.. note::
    Using Cloud Robusta UI is the simplest option. It is preferred by most organizations.

Self hosted architecture
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Robusta backend consists of the following components, installed via a `helm chart <https://helm.sh/>`_, on a Kubernetes cluster of your choice:

- `Supabase <https://supabase.com/>`_: stores all alerts and troubleshooting data in a Postgres DB. Handles user authentication.
- Robusta UI Frontend: alerting dashboard built just for Kubernetes.
- Robusta Relay: handles Slack integration and more.

In addition to the backend services, an installation of the base Robusta OSS project is required, on one or more clusters.

Instead of using the cloud backend services, the Robusta OSS project will be directed to the self hosted backend instance.


.. image:: ../images/self_host_diagram.png
   :align: center

Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To install the Robusta self hosted instance, please contact support@robusta.dev, or post in the #support channel of `our Slack community <https://join.slack.com/t/robustacommunity/shared_invite/zt-18x24hrz4-1SQQCSa~AF9LgTYFwA6cag>`_.

