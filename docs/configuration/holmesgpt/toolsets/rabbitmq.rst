.. _toolset_prometheus:

RabbitMQ
========

By enabling this toolset, HolmesGPT will be able to detect RabbitMQ partitions, memory alerts and disk alerts and suggest mitigations.

This toolset follows a two step process to detect partition:

1. The nodes and partitioning status is obtained by fetching information from the configured ``management_url``.
2. If some nodes are reported as not-running, the toolset will try to contact these nodes individually and deduct any partitioning 
   state for any node that is actually running.


Configuration
-------------

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chat

    .. code-block:: yaml

      holmes:
        toolsets:
          rabbitmq/core:
            enabled: true
            config:
              clusters:
                - id: rabbitmq # must be unique across all configured clusters
                  username: <user>
                  password: <password>
                  management_url: <http://rabbitmq.rabbitmq:15672>


    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    Add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

      toolsets:
        rabbitmq/core:
          enabled: true
          config:
            clusters:
              - id: rabbitmq # must be unique across all configured clusters
                username: <user>
                password: <password>
                management_url: <http://rabbitmq.rabbitmq:15672>


**Advanced configuration**

Below is the full list of options for this toolset:

.. code-block:: yaml

  rabbitmq/core:
    enabled: true
    config:
      clusters:
        - id: rabbitmq # must be unique across all configured clusters
          username: <user>
          password: <password>
          management_url: <http://rabbitmq.rabbitmq:15672>
          request_timeout_seconds: 30 # timeout for the API requests to RabbitMQ
          verify_certs: True # if the management API is https and the certificate is not valid


- **id** A unique identifier for this cluster. Holmes uses it to figure out what cluster to check when answering a question or investigating an alert.
- **username** A username to authenticate against the management API
- **password** A pasword to authenticate against the management API
- **management_url** The base URL for this RabbitMQ's cluster. Typically you would want to put the URL of the RabbitMQ service ``http://rabbitmq.rabbitmq:15672``.
- **request_timeout_seconds** The timeout in seconds for the API requests to RabbitMQ.
- **verify_certs** Set to False if RabbitMQ exposes the API through self signed certificates.


Capabilities
------------
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - list_configured_clusters
     - List all configured clusters. Useful to get the id of a configured cluster (cluster_id) and pass as argument to other rabbitmq tool calls.
   * - get_rabbitmq_cluster_status
     - Fetches the overall status of the RabbitMQ cluster, including node information, listeners, and partition details. Crucial for detecting split-brain scenarios (network partitions).
