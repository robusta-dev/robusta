Docker
======

**This integration is not recommended for monitoring a kubernetes cluster because it
is neither necessary nor useful.** It is documented here for users of HolmesGPT CLI.

Read access to Docker resources.

Configuration
-------------

.. code-block:: yaml

    holmes:
        toolsets:
            docker/core:
                enabled: true

.. include:: ./_toolset_configuration.inc.rst

Capabilities
------------
.. include:: ./_toolset_capabilities.inc.rst

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
