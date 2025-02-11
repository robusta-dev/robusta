Docker
======

Read access to Docker resources

To enable this integration, update the Helm values for Robusta (generated_values.yaml).

.. code-block:: yaml

    # Example Configuration:
    holmes:

        toolsets:
            docker/core:
                enabled: true

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - docker_images
     - List all Docker images
   * - docker_ps
     - List all running Docker containers
   * - docker_ps_all
     - List all Docker containers, including stopped ones
   * - docker_inspect
     - Inspect detailed information about a Docker container or image
   * - docker_logs
     - Fetch the logs of a Docker container
   * - docker_top
     - Display the running processes of a container
   * - docker_events
     - Get real-time events from the Docker server
   * - docker_history
     - Show the history of an image
   * - docker_diff
     - Inspect changes to files or directories on a container's filesystem
