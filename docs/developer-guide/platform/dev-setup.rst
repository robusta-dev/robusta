Setup
###################################################

These are instructions for developing Robusta's core platform.


Most users are looking for the regular :ref:`Installation` or the documentation on :ref:`Writing Playbook Actions`.
For developing Robusta itself, read on!

Installing Robusta in-cluster from source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. ``git clone`` the source code.
2. Install `skaffold <https://skaffold.dev/>`_ and `helm <https://helm.sh/>`_
3. Run ``robusta gen-config`` and copy the result to ``deployment/generated_values.yaml``
4. Run ``skaffold run --tail``, or ``skaffold run --tail -p apple-m1-dev`` if you're using Apple M1

Common errors
---------------
* If you encounter an error like: ``"https://prometheus-community.github.io/helm-chart" is not a valid chart repository or cannot be reached`` then run:

.. code-block:: bash

    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

* If you're on Mac OS and receive errors about Pillow or libjpeg when running ``poetry install`` then run ``brew install libjpeg`` first.

* If you encounter ``NotADirectoryError: [Errno 20] Not a directory`` while trying to debug, you may need to disable the ``Attach to subprocess`` option on your debugger.

For faster builds that are running on Google Cloud
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Install `gcloud <https://cloud.google.com/sdk/docs/install/>`_
2. Run ``gcloud auth application-default login``
3. Now when you want to build:
    a. Run ``skaffold run -p gcloud-build``

Running Robusta locally
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is never necessary, but you might find it more convenient to run Robusta locally and not in cluster.

1. ``git clone`` the source code
2. ``poetry install``
3. ``poetry run python3 -m robusta.runner.main``
4. Consider using `telepresence <https://www.telepresence.io/>`_ to connect your local Robusta process with in-cluster services like Prometheus.

Running Robusta cli locally
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This is only necessary if you are developing features for the cli itself.

Using poetry
----------------
1. ``git clone`` the source code
2. ``poetry install``
3. ``poetry run robusta``

Alternative method using pip
-----------------------------

This method installs robusta into your global python environment

1. ``git clone`` the source code
2. ``pip3 install .``

Running Tests
^^^^^^^^^^^^^^^^^^^^
See ``tests/README.md``
