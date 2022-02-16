Documentation contributions
###################################################

These are instructions for contributing to Robusta's documentation.

Robusta's docs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These docs are Sphinx docs.

Currently it's all manual docs, but at a later phase can crawl the python code, and auto generate additional docs.

Github actions build & deploy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The docs are deployed into a public gcp bucket.

Any push to docs/* will trigger a github workflow, that will build the docs to 'master' (https://docs.robusta.dev/master)
Creating a code release will build and deploy docs release too. (for example: https://docs.robusta.dev/0.4.26)

If you need to override an existing doc release, you can manually trigger the workflow, with the release version as a parameter.

Local Build
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The docs definitions are ``.rst`` files.

Learn more about ``.rst`` files `here <https://learnxinyminutes.com/docs/rst/>`_

Prerequisites to be present on your local machine:

* `Python <https://www.python.org/downloads/>`_
* `Poetry <https://python-poetry.org/docs/>`_
* `Sphinx <https://www.sphinx-doc.org/en/master/usage/installation.html>`_

First install the build requirements:

.. code-block:: bash

   poetry install -E all

To build the html and develop locally run the script:

.. code-block:: bash

   ./docs_autobuild.sh

Note: If you're on windows, run the contents of the ``docs_autobuild.sh`` manually.

Run ``make help`` inside the ``docs`` directory for more options for working with sphinx.

Troubleshooting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. ``poetry: command not found`` - Make sure you have `Poetry <https://python-poetry.org/docs/>`_ installed and run ``source $HOME/.poetry/env`` in Linux environments to set the poetry environment variables.

2. ``sphinx-build: command not found`` - Make sure you have `Sphinx <https://www.sphinx-doc.org/en/master/usage/installation.html>`_ installed.
