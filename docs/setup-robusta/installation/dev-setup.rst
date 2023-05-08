Build from Source
###################################################

Install Robusta from source to develop new features for the Robusta Engine (robusta-runner).

To install Robusta as a user, follow :ref:`install-all-in-one` instead.

To develop new playbook actions, you don't need to install from source. Refer to :ref:`Developing New Actions`.

Using Skaffold
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. ``git clone`` the source code.
2. Install `skaffold <https://skaffold.dev/>`_ and `helm <https://helm.sh/>`_
3. Run ``helm repo add prometheus-community https://prometheus-community.github.io/helm-charts``
4. Run ``robusta gen-config`` and copy the result to ``deployment/generated_values.yaml``
5. Run ``skaffold run --tail``. On M1 Macs, add ``-p apple-m1-dev``

.. details:: Common Errors

    .. tab-set::

        .. tab-item:: Pillow/libjpeg Errors

            Occurs on Mac OS if dependencies are missing. Run ``brew install libjpeg``.

        .. tab-item:: NotADirectoryError: [Errno 20]

            Sometimes, when attaching a debugger to Robusta the following error occurs: ``NotADirectoryError: [Errno 20] Not a directory``

            If this occurs, disable the ``Attach to subprocess`` option on your debugger.

.. details:: Want Faster Builds? ⚡️

    1. Install `gcloud <https://cloud.google.com/sdk/docs/install/>`_
    2. Run ``gcloud auth application-default login``
    3. Build with ``skaffold run -p gcloud-build``

Local Development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When :ref:`Using Skaffold`, Robusta runs inside a Kubernetes cluster.

For faster code changes, you can run Robusta on your local computer:

1. ``git clone`` the source code
2. Run ``./run_runner_locally.sh``

.. note::

    You must have a cluster with Robusta installed for this to work. The runner needs a configuration file to run and it extracts it from your existing cluster.

Additional tips:

* If you want to develop playbooks locally, configure ``playbookRepos`` with a local path to your playbooks directory.
* Your local runner wont incoming Kubernetes changes or Prometheus alerts.
* For instructions on simulating Prometheus alerts, try ``poetry run robusta playbooks trigger --dry-run prometheus_alert alert_name=KubePodCrashLooping namespace=default pod_name=example-pod``

CLI Development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To develop the ``robusta`` cli:

1. ``git clone`` the source code
2. ``poetry install``
3. ``poetry run robusta``

.. details:: Alternative method, using pip not poetry

    Install the ``robusta`` cli into your global python environment:

    1. ``git clone`` the source code
    2. ``pip3 install .``

Running Tests
^^^^^^^^^^^^^^^^^^^^
See ``tests/README.md``