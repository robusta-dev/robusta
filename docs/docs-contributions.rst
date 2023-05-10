Improving These Docs
###################################################

These docs are generated with `Sphinx <https://www.sphinx-doc.org/en/master/>`_

Writing Docs
^^^^^^^^^^^^^

Our docs are written in RST format. Learn more about RST `here <https://learnxinyminutes.com/docs/rst/>`_

Building Docs Locally
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Prerequisites
----------------

The following must be installed on your local machine:

* `Python <https://www.python.org/downloads/>`_
* `Poetry <https://python-poetry.org/docs/>`_

Instructions
----------------

Clone Robusta's repository:

.. code-block:: bash

   git clone https://github.com/robusta-dev/robusta.git && cd robusta

Install all devlopment requirements:

.. code-block:: bash

   poetry install -E all

Build the docs locally:

.. code-block:: bash

   ./docs_autobuild.sh

.. details:: Instructions for Windows

    Instead of running ``./docs_autobuild.sh``, copy-paste the commands inside of it and run them manually.

.. details:: Common Errors

    1. ``poetry: command not found`` - Make sure you have `Poetry <https://python-poetry.org/docs/>`_ installed and run ``source $HOME/.poetry/env`` in Linux environments to set the poetry environment variables.

    2. ``sphinx-build: command not found`` - Make sure you have `Sphinx <https://www.sphinx-doc.org/en/master/usage/getting-started/installation.html>`_ installed.

    3. ``OSError: [Errno 98] Address already in use`` - Use the ``--port <Number>`` argument, with a port of your choice. Example: ``./docs_autobuild.sh --port 8822``

Deploying the Docs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These docs are automatically deployed on every commit.

On every push to ``docs/*``, a GitHub action builds and deploys docs to https://docs.robusta.dev/<branch-name>

On every release, a GitHub action builds and deploys docs to https://docs.robusta.dev/<version>

If you need to override an existing docs release, you can manually trigger the workflow.
