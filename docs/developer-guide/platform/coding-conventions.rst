Coding Conventions
###################################################

The following guidelines apply to code contributions to the Robusta engine itself.

Formatting and coding conventions
------------------------------------
Robusta uses `Black <https://github.com/psf/black>`_ to automatically format code. Please set up Black prior so that all
your contributions to Robusta will be formatted properly.

To do so, install Robusta's dependencies with ``cd src/ && poetry install`` and then install the hook by running ``pre-commit install``

For instructions on using Black with your IDE, `see Black's documentation. <https://black.readthedocs.io/en/stable/integrations/editors.html>`_

Data classes
-------------------------------------
Use pydantic.BaseModel instead of Python dataclasses when possible. Pydantic performs datavalidation whereas Python dataclasses just reduce boilerplate code like defining __init__()
