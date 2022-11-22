Setup with DockerHub
======================

Instructions to setup Robusta developement environment using `Docker Hub <https://hub.docker.com/>`_ and any Kubernetes cluster.

Initial Setup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. ``git clone`` the source code.
2. Install `skaffold <https://skaffold.dev/>`_ and `helm <https://helm.sh/>`_
3. Run ``robusta gen-config`` and copy the result to ``deployment/generated_values.yaml``
4. Run ``docker login`` and log into your Docker Hub account.
5. Finally create your Kubernetes cluster, and add it to your **KUBECONFIG**.

Building
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Add this code at the end of your **skaffold.yaml** file.


.. code-block:: yaml

   - name: local-build
     build:
      artifacts:
      - image: DockerHubUserName/robusta-runner-build
        context: .
        docker:
          dockerfile: Dockerfile

Replace `DockerHubName` with your Docker Hub Username.

2. Next replace  ..code ``us-central1-docker.pkg.dev/genuine-flight-317411/devel/robusta-runner`` in build -> artifacts -> image and  artifactOverrides -> runner.image with ``DockerHubUserName/robusta-runner-build``

 .. image:: /images/local_dev_setup_skaffold.png
              :width: 600
              :align: center

3. To build and deploy local changes run

.. code-block:: bash

  skaffold run -p local-build

Alernatively you can use 

.. code-block:: bash

  skaffold dev -p local-build 

To continuously build and deploy. 